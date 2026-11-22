"""SMM Background Worker: Dual-Mode Clip Generator & Multi-Platform Scheduler (Slice 3B)."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.smm import SmmClipJobModel, SmmSettingsModel
from app.infrastructure.db.models.translation import MovieTranslationModel
from scraper.smm_pipeline import create_smart_smm_clip
from scraper.smm_publishers.dispatcher import MultiPlatformDispatcher
from scraper.smm_publishers.telegram_pub import TelegramChannelPublisher, build_movie_caption

logger = logging.getLogger(__name__)


def is_schedule_due(
    schedule_hours: List[str],
    now: datetime,
    last_published_at: Optional[datetime],
    daily_count: int,
    daily_limit: int,
) -> bool:
    """Return True when daily quota remains and current HH:00 slot has not yet published."""
    if daily_count >= daily_limit or not schedule_hours:
        return False
    cur_hhmm = now.strftime("%H:%M")
    cur_hour = now.strftime("%H:")
    slot_match = any(s == cur_hhmm or s.startswith(cur_hour) for s in schedule_hours)
    if not slot_match:
        return False
    if last_published_at and last_published_at.strftime("%Y-%m-%d %H") == now.strftime("%Y-%m-%d %H"):
        return False
    return True


async def enqueue_smm_clip_job(
    db: AsyncSession,
    movie_code: str,
    title: str,
    media_id: Optional[int] = None,
    media_type: str = "movie",
    start_sec: float = 0.0,
) -> SmmClipJobModel:
    """Enqueue a clip generation job if an active job for movie_code does not already exist."""
    existing = (
        await db.execute(
            select(SmmClipJobModel).where(
                SmmClipJobModel.movie_code == movie_code,
                SmmClipJobModel.status.in_(("generating", "waiting_approval", "scheduled", "publishing")),
            )
        )
    ).scalar_one_or_none()
    if existing:
        return existing

    cfg = (await db.execute(select(SmmSettingsModel).where(SmmSettingsModel.id == 1))).scalar_one_or_none()
    duration = float(cfg.clip_duration_sec) if cfg else 45.0
    platforms = {p: {"enabled": True, "status": "pending", "post_id": None, "error": None} for p in (cfg.enabled_platforms if cfg else ["telegram"])}
    job = SmmClipJobModel(
        media_type=media_type, media_id=media_id, movie_code=movie_code,
        title=title, start_sec=start_sec, duration_sec=duration,
        status="generating", platforms_status=platforms,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


async def maybe_enqueue_smm_for_movie(
    db: AsyncSession,
    movie_id: int,
    movie_code: str,
    title: str,
) -> Optional[SmmClipJobModel]:
    """Enqueue Cycle 2 SMM clip job behind SMM_AUTOPILOT_ENABLED guard without risking Cycle 1 commit."""
    flag = os.getenv("SMM_AUTOPILOT_ENABLED", "").strip().lower()
    if flag not in {"1", "true", "yes", "on"}:
        return None
    try:
        async with db.begin_nested():
            return await enqueue_smm_clip_job(
                db=db,
                movie_code=movie_code,
                title=title,
                media_id=movie_id,
                media_type="movie",
            )
    except Exception as exc:
        logger.warning("SMM enqueue skipped for movie #%s (%s): %s", movie_code, movie_id, exc)
        return None


async def process_generating_job(
    db: AsyncSession,
    job: SmmClipJobModel,
    cfg: SmmSettingsModel,
    tg_client: Any,
    storage_chat_id: int | str,
    uploads_dir: str = "uploads/smm",
) -> SmmClipJobModel:
    """Fetch Storage video message, render 9:16 clip, and move job to waiting_approval/scheduled."""
    movie = (await db.execute(select(MovieModel).where(MovieModel.id == job.media_id))).scalar_one_or_none() if job.media_id else None
    trans = (
        await db.execute(
            select(MovieTranslationModel).where(
                MovieTranslationModel.movie_id == job.media_id,
                MovieTranslationModel.storage_channel_message_id.isnot(None),
            )
        )
    ).scalars().first()
    if not trans or not trans.storage_channel_message_id:
        job.status = "failed"
        await db.flush()
        return job

    display_code = getattr(movie, "short_code", None) or job.movie_code
    bot_handle = cfg.bot_username or "@MediaPlusOfficialBot"
    storage_msg = await tg_client.get_messages(storage_chat_id, ids=trans.storage_channel_message_id)
    out_file = os.path.join(uploads_dir, f"clip_{job.id}.mp4")
    meta = await create_smart_smm_clip(
        client=tg_client, storage_msg=storage_msg, output_path=out_file,
        movie_code=display_code, imdb_rating=getattr(movie, "imdb_rating", None),
        duration_sec=job.duration_sec or cfg.clip_duration_sec,
        start_sec=job.start_sec if job.start_sec > 0 else None,
        copyright_shield=cfg.copyright_shield,
        bot_username=bot_handle,
    )
    job.start_sec = float(meta["start_sec"])
    job.duration_sec = float(meta["duration_sec"])
    job.clip_path = f"uploads/smm/clip_{job.id}.mp4"
    job.caption = job.caption or build_movie_caption(
        movie_code=display_code, imdb_rating=getattr(movie, "imdb_rating", None),
        genres=getattr(movie, "genres", None), bot_username=bot_handle,
    )
    job.status = "scheduled" if cfg.mode == "FULL_AUTO" else "waiting_approval"
    await db.flush()
    await db.refresh(job)
    return job


async def process_publish_job(
    db: AsyncSession,
    job: SmmClipJobModel,
    cfg: SmmSettingsModel,
    dispatcher: Optional[MultiPlatformDispatcher] = None,
    base_public_url: str = "",
) -> SmmClipJobModel:
    """Publish rendered clip across enabled platforms and save per-platform results."""
    bot_handle = cfg.bot_username or "@MediaPlusOfficialBot"
    movie = (await db.execute(select(MovieModel).where(MovieModel.id == job.media_id))).scalar_one_or_none() if job.media_id else None
    display_code = getattr(movie, "short_code", None) or job.movie_code

    if not dispatcher:
        dispatcher = MultiPlatformDispatcher()
        if cfg.telegram_channel_id:
            dispatcher.publishers["telegram"] = TelegramChannelPublisher(
                channel_id=cfg.telegram_channel_id, bot_username=bot_handle
            )

    video_url = f"{base_public_url.rstrip('/')}/{job.clip_path}" if base_public_url and job.clip_path else ""
    results = await dispatcher.publish_all(
        video_path=job.clip_path or "", caption=job.caption or "",
        movie_code=display_code, platforms=cfg.enabled_platforms, video_url=video_url,
        bot_username=bot_handle,
    )
    status_map = dict(job.platforms_status or {})
    any_ok = False
    for plat, res in results.items():
        any_ok = any_ok or res.success
        status_map[plat] = {"enabled": True, "status": "published" if res.success else "failed", "post_id": res.post_id, "error": res.error}

    job.platforms_status = status_map
    job.status = "completed" if any_ok else "failed"
    await db.flush()
    await db.refresh(job)
    return job


async def run_smm_worker_tick(
    db: AsyncSession,
    tg_client: Any = None,
    storage_chat_id: int | str = 0,
    base_public_url: str = "",
) -> dict:
    """Execute one non-blocking SMM worker tick (generate 1 clip + publish 1 due job)."""
    cfg = (await db.execute(select(SmmSettingsModel).where(SmmSettingsModel.id == 1))).scalar_one_or_none()
    if not cfg:
        return {"generated": 0, "published": 0}

    generated, published = 0, 0
    gen_job = (await db.execute(select(SmmClipJobModel).where(SmmClipJobModel.status == "generating").limit(1))).scalar_one_or_none()
    if gen_job and tg_client and storage_chat_id:
        await process_generating_job(db, gen_job, cfg, tg_client, storage_chat_id)
        generated = 1

    pub_job = (await db.execute(select(SmmClipJobModel).where(SmmClipJobModel.status == "publishing").limit(1))).scalar_one_or_none()
    if not pub_job and cfg.mode == "FULL_AUTO":
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        daily_cnt = (await db.execute(select(func.count()).select_from(SmmClipJobModel).where(SmmClipJobModel.status == "completed", SmmClipJobModel.updated_at >= today_start))).scalar() or 0
        last_pub = (await db.execute(select(func.max(SmmClipJobModel.updated_at)).where(SmmClipJobModel.status == "completed"))).scalar()
        if is_schedule_due(cfg.schedule_hours, now, last_pub, int(daily_cnt), cfg.daily_limit):
            pub_job = (await db.execute(select(SmmClipJobModel).where(SmmClipJobModel.status == "scheduled").order_by(SmmClipJobModel.id.asc()).limit(1))).scalar_one_or_none()

    if pub_job:
        await process_publish_job(db, pub_job, cfg, base_public_url=base_public_url)
        published = 1
    return {"generated": generated, "published": published}


def resolve_smm_session_string() -> str:
    """Return dedicated SMM_TELEGRAM_STRING_SESSION; refuse shared scraper session unless explicitly allowed."""
    dedicated = os.getenv("SMM_TELEGRAM_STRING_SESSION", "").strip()
    if dedicated:
        return dedicated
    if os.getenv("SMM_ALLOW_SHARED_SESSION", "").strip().lower() in {"1", "true", "yes", "on"}:
        return os.getenv("TELEGRAM_STRING_SESSION", "").strip()
    return ""


async def run_smm_worker_cycle(
    tg_client: Any = None,
    session_factory: Any = None,
) -> dict:
    """Run one safe DB-committed SMM worker tick behind SMM_AUTOPILOT_ENABLED."""
    if os.getenv("SMM_AUTOPILOT_ENABLED", "").strip().lower() not in {"1", "true", "yes", "on"}:
        return {"generated": 0, "published": 0, "skipped": True}
    if session_factory is None:
        from app.infrastructure.db.session import async_session_factory
        session_factory = async_session_factory
    raw_chat = os.getenv("STORAGE_CHANNEL_ID", "0").strip()
    storage_chat_id: int | str = int(raw_chat) if raw_chat.lstrip("-").isdigit() else raw_chat
    base_public_url = os.getenv("PUBLIC_API_BASE_URL", "https://kinochi-project-alpha-9g6j.onrender.com").strip()

    async with session_factory() as db:
        res = await run_smm_worker_tick(
            db, tg_client=tg_client, storage_chat_id=storage_chat_id, base_public_url=base_public_url
        )
        await db.commit()
        return res


async def supervised_run_smm_worker() -> None:
    """Long-running background supervisor for Cycle 2 SMM rendering and publishing."""
    interval = max(30, int(os.getenv("SMM_WORKER_INTERVAL_SEC", "180")))
    tg_client = None
    session_disabled = False

    while True:
        try:
            enabled = os.getenv("SMM_AUTOPILOT_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}
            if enabled:
                sess = "" if session_disabled else resolve_smm_session_string()
                api_id = os.getenv("TELEGRAM_API_ID", "").strip()
                api_hash = os.getenv("TELEGRAM_API_HASH", "").strip()
                if sess and api_id.isdigit() and api_hash and tg_client is None:
                    from telethon import TelegramClient
                    from telethon.sessions import StringSession
                    tg_client = TelegramClient(StringSession(sess), int(api_id), api_hash)
                    await tg_client.connect()
                await run_smm_worker_cycle(tg_client=tg_client)
        except (KeyboardInterrupt, asyncio.CancelledError):
            if tg_client:
                try:
                    await tg_client.disconnect()
                except Exception:
                    pass
            raise
        except Exception as exc:
            if "AuthKeyDuplicated" in type(exc).__name__ or "AuthKeyDuplicated" in str(exc):
                session_disabled = True
                tg_client = None
            logger.warning("SMM worker tick error (API/Bot isolated): %s", exc)
        await asyncio.sleep(interval)
