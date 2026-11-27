"""SMM Background Worker: Dual-Mode Clip Generator & Multi-Platform Scheduler (Slice 3B)."""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, List, Optional

from sqlalchemy import case, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import EpisodeModel, SeasonModel, SeriesModel
from app.infrastructure.db.models.smm import SmmClipJobModel, SmmSettingsModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel, MovieTranslationModel
from scraper.smm_clipper import download_sparse_clip_source
from scraper.smm_pipeline import _fetch_poster_bytes, create_smart_smm_clip
from scraper.smm_publishers.dispatcher import MultiPlatformDispatcher
from scraper.smm_publishers.telegram_pub import (
    TelegramChannelPublisher,
    _post_telegram_video,
    build_movie_caption,
    send_admin_alert,
    send_admin_smm_preview,
)
from scraper.smm_rubric_engine import create_rubric_smm_clip
from scraper.smm_rubric_planner import RUBRIC_MODES, pick_rubric_media, select_weekly_rubric

logger = logging.getLogger(__name__)

_WORKER_STATE: dict[str, Any] = {
    "running": False,
    "started_at": None,
    "last_tick_at": None,
    "last_error": None,
    "last_result": None,
}


def get_smm_worker_state() -> dict[str, Any]:
    """Return non-secret SMM background worker runtime state for /smm/progress diagnostics."""
    return {
        "enabled": os.getenv("SMM_AUTOPILOT_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"},
        "has_smm_session": bool(resolve_smm_session_string()),
        "has_api_id": os.getenv("TELEGRAM_API_ID", "").strip().isdigit(),
        "has_storage_id": bool(os.getenv("STORAGE_CHANNEL_ID", "").strip()),
        **dict(_WORKER_STATE),
    }


TASHKENT_TZ = timezone(timedelta(hours=5))


def is_schedule_due(
    schedule_hours: List[str],
    now: datetime,
    last_published_at: Optional[datetime],
    daily_count: int,
    daily_limit: int,
    monthly_count: int = 0,
    monthly_limit: int = 90,
) -> bool:
    """Return True when daily/monthly quota remains and current HH:00 slot has not yet published."""
    if daily_count >= daily_limit or monthly_count >= monthly_limit or not schedule_hours:
        return False
    cur_hhmm = now.strftime("%H:%M")
    cur_hour = now.strftime("%H:")
    slot_match = any(s == cur_hhmm or s.startswith(cur_hour) for s in schedule_hours)
    if not slot_match:
        return False
    if last_published_at:
        last_cmp = (
            last_published_at.astimezone(now.tzinfo)
            if (now.tzinfo and last_published_at.tzinfo)
            else last_published_at
        )
        if last_cmp.strftime("%Y-%m-%d %H") == now.strftime("%Y-%m-%d %H"):
            return False
    return True


async def auto_pick_catalog_movie(db: AsyncSession, now_local: Optional[datetime] = None) -> Optional[SmmClipJobModel]:
    """Select weekly rubric media on prime evening slots (Mon/Wed/Fri/Sun) or high-retention gem movie."""
    if now_local is not None:
        day_start = now_local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
        week_start = (now_local - timedelta(days=now_local.weekday())).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
        today_modes = list((await db.execute(select(SmmClipJobModel.clip_mode).where(SmmClipJobModel.created_at >= day_start))).scalars().all())
        week_modes = list((await db.execute(select(SmmClipJobModel.clip_mode).where(SmmClipJobModel.created_at >= week_start))).scalars().all())
        rubric = select_weekly_rubric(now_local, completed_today=today_modes, completed_week=week_modes)
        if rubric in RUBRIC_MODES:
            picked = await pick_rubric_media(db, rubric)
            if picked:
                return await enqueue_smm_clip_job(
                    db=db,
                    movie_code=picked["movie_code"],
                    title=picked["title"],
                    media_id=picked["media_id"],
                    media_type="movie",
                    clip_mode=rubric,
                )
    used_ids = select(SmmClipJobModel.media_id).where(
        SmmClipJobModel.media_type == "movie",
        SmmClipJobModel.media_id.isnot(None),
    )
    used_codes = select(SmmClipJobModel.movie_code)
    has_storage = exists(
        select(MovieTranslationModel.id).where(
            MovieTranslationModel.movie_id == MovieModel.id,
            MovieTranslationModel.storage_channel_message_id.isnot(None),
        )
    )
    quality_gate = or_(
        MovieModel.imdb_rating.is_(None),
        MovieModel.imdb_rating >= 5.8,
        MovieModel.release_year >= 2023,
    )
    genres_l = func.lower(func.coalesce(MovieModel.genres, ""))
    high_retention = or_(
        genres_l.contains("triller"),
        genres_l.contains("thriller"),
        genres_l.contains("jangari"),
        genres_l.contains("ekshn"),
        genres_l.contains("action"),
        genres_l.contains("fantastika"),
        genres_l.contains("sci-fi"),
        genres_l.contains("anime"),
        genres_l.contains("sirli"),
        genres_l.contains("mystery"),
        genres_l.contains("kriminal"),
        genres_l.contains("sarguzasht"),
    )
    gem_score = (
        func.coalesce(MovieModel.imdb_rating, 0.0) * 10.0
        + case((MovieModel.release_year >= 2023, 25.0), else_=0.0)
        + case((high_retention, 18.0), else_=0.0)
        + func.coalesce(MovieModel.view_count, 0) * 2.0
    )
    stmt = (
        select(MovieModel)
        .where(
            MovieModel.publish_status == "published",
            quality_gate,
            has_storage,
            MovieModel.id.notin_(used_ids),
            func.coalesce(MovieModel.short_code, MovieModel.code).notin_(used_codes),
            MovieModel.code.notin_(used_codes),
        )
        .order_by(
            gem_score.desc(),
            func.coalesce(MovieModel.release_year, 0).desc(),
            MovieModel.id.desc(),
        )
        .limit(1)
    )
    movie = (await db.execute(stmt)).scalar_one_or_none()
    if not movie:
        return None
    pick_code = (getattr(movie, "short_code", None) or movie.code or "").strip()
    if not pick_code:
        return None
    return await enqueue_smm_clip_job(
        db=db,
        movie_code=pick_code,
        title=movie.title,
        media_id=movie.id,
        media_type="movie",
    )


async def enqueue_smm_clip_job(
    db: AsyncSession,
    movie_code: str,
    title: str,
    media_id: Optional[int] = None,
    media_type: str = "movie",
    start_sec: float = 0.0,
    clip_mode: str = "scene",
    hook_text: Optional[str] = None,
    duration_sec: Optional[float] = None,
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
    duration = float(duration_sec) if duration_sec is not None else float(cfg.clip_duration_sec if cfg else 28.0)
    platforms = {p: {"enabled": True, "status": "pending", "post_id": None, "error": None} for p in (cfg.enabled_platforms if cfg else ["telegram"])}
    job = SmmClipJobModel(
        media_type=media_type, media_id=media_id, movie_code=movie_code,
        title=title, clip_mode=clip_mode, hook_text=hook_text,
        start_sec=start_sec, duration_sec=duration,
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


async def _resolve_job_media(
    db: AsyncSession,
    job: SmmClipJobModel,
) -> tuple[str, Optional[float], Optional[str], Optional[int]]:
    """Resolve (display_code, imdb_rating, genres, storage_msg_id) for movie or episode jobs."""
    if job.media_type == "episode":
        ep_filter = (
            EpisodeModel.id == job.media_id
            if job.media_id
            else or_(EpisodeModel.short_code == job.movie_code, EpisodeModel.code == job.movie_code)
        )
        ep = (await db.execute(select(EpisodeModel).where(ep_filter))).scalars().first()
        series = None
        trans = None
        if ep:
            season = (await db.execute(select(SeasonModel).where(SeasonModel.id == ep.season_id))).scalar_one_or_none()
            if season:
                series = (await db.execute(select(SeriesModel).where(SeriesModel.id == season.series_id))).scalar_one_or_none()
            trans = (
                await db.execute(
                    select(EpisodeTranslationModel).where(
                        EpisodeTranslationModel.episode_id == ep.id,
                        EpisodeTranslationModel.storage_channel_message_id.isnot(None),
                    )
                )
            ).scalars().first()
        display_code = (getattr(ep, "short_code", None) if ep else None) or (getattr(ep, "code", None) if ep else None) or job.movie_code
        return (
            display_code,
            getattr(series, "imdb_rating", None) if series else None,
            getattr(series, "genres", None) if series else None,
            trans.storage_channel_message_id if trans else None,
        )

    m_filter = (
        MovieModel.id == job.media_id
        if job.media_id
        else or_(MovieModel.short_code == job.movie_code, MovieModel.code == job.movie_code)
    )
    movie = (await db.execute(select(MovieModel).where(m_filter))).scalars().first()
    trans = None
    if movie:
        trans = (
            await db.execute(
                select(MovieTranslationModel).where(
                    MovieTranslationModel.movie_id == movie.id,
                    MovieTranslationModel.storage_channel_message_id.isnot(None),
                )
            )
        ).scalars().first()
    display_code = getattr(movie, "short_code", None) or job.movie_code
    return (
        display_code,
        getattr(movie, "imdb_rating", None) if movie else None,
        getattr(movie, "genres", None) if movie else None,
        trans.storage_channel_message_id if trans else None,
    )


async def _resolve_scene_meta(db: AsyncSession, job: SmmClipJobModel) -> dict[str, Any]:
    """Resolve optional TMDb/episode metadata for SRT iconic-scene lookup."""
    if job.media_type == "episode":
        ep_filter = EpisodeModel.id == job.media_id if job.media_id else or_(EpisodeModel.short_code == job.movie_code, EpisodeModel.code == job.movie_code)
        ep = (await db.execute(select(EpisodeModel).where(ep_filter))).scalars().first()
        if not ep:
            return {}
        season = (await db.execute(select(SeasonModel).where(SeasonModel.id == ep.season_id))).scalar_one_or_none()
        series = (await db.execute(select(SeriesModel).where(SeriesModel.id == season.series_id))).scalar_one_or_none() if season else None
        return {
            "tmdb_id": getattr(series, "tmdb_id", None) if series else None,
            "original_title": getattr(series, "title", None) if series else job.title,
            "content_type": "tv",
            "season_number": getattr(season, "season_number", None) if season else None,
            "episode_number": getattr(ep, "episode_number", None),
        }
    m_filter = MovieModel.id == job.media_id if job.media_id else or_(MovieModel.short_code == job.movie_code, MovieModel.code == job.movie_code)
    movie = (await db.execute(select(MovieModel).where(m_filter))).scalars().first()
    return {
        "tmdb_id": getattr(movie, "tmdb_id", None) if movie else None,
        "original_title": (getattr(movie, "original_title", None) or getattr(movie, "title", None) or job.title) if movie else job.title,
        "content_type": "movie",
    }


async def _ensure_localized_poster_url(
    db: AsyncSession,
    media: Any,
    content_type: str,
    code: Optional[str] = None,
    topic_chat_id: Optional[int | str] = None,
    topic_id: Optional[int] = None,
) -> Optional[str]:
    """Ensure media poster is Uzbek-localized in Telegram storage before rendering SMM clip cover."""
    if not media:
        return None
    current = (getattr(media, "poster_url", None) or "").strip()
    if "/api/v1/posters/tg/" in current:
        return current
    tmdb_id = getattr(media, "tmdb_id", None)
    if not tmdb_id and not current:
        return None
    try:
        from app.core.cache import delete_cache_pattern
        from app.infrastructure.external.poster_localizer import localize_poster_and_upload

        localized = await localize_poster_and_upload(
            title=str(getattr(media, "title", "") or ""),
            tmdb_id=tmdb_id,
            content_type=content_type,
            manual_poster_url=current or None,
            code=code,
            topic_chat_id=topic_chat_id,
            topic_id=topic_id,
        )
        if localized:
            media.poster_url = localized
            await db.flush()
            try:
                prefix = "cache:series:*" if content_type == "tv" else "cache:movies:*"
                await delete_cache_pattern(prefix)
                await delete_cache_pattern("cache:search:*")
            except Exception as cache_exc:
                logger.debug("Poster cache invalidation skipped: %s", cache_exc)
            return localized
    except Exception as exc:
        logger.warning("SMM poster cover auto-localization fallback for %s: %s", getattr(media, "title", ""), exc)
    return current or None


async def _resolve_media_poster_url(db: AsyncSession, job: SmmClipJobModel) -> Optional[str]:
    """Fetch (and localize if needed) poster_url for movie or parent series of an episode job."""
    if job.media_type == "episode":
        ep_filter = EpisodeModel.id == job.media_id if job.media_id else or_(EpisodeModel.short_code == job.movie_code, EpisodeModel.code == job.movie_code)
        ep = (await db.execute(select(EpisodeModel).where(ep_filter))).scalars().first()
        if not ep:
            return None
        season = (await db.execute(select(SeasonModel).where(SeasonModel.id == ep.season_id))).scalar_one_or_none()
        series = (await db.execute(select(SeriesModel).where(SeriesModel.id == season.series_id))).scalar_one_or_none() if season else None
        return await _ensure_localized_poster_url(db, series, content_type="tv")
    m_filter = MovieModel.id == job.media_id if job.media_id else or_(MovieModel.short_code == job.movie_code, MovieModel.code == job.movie_code)
    movie = (await db.execute(select(MovieModel).where(m_filter))).scalars().first()
    if not movie:
        return None
    return await _ensure_localized_poster_url(
        db,
        movie,
        content_type="movie",
        code=getattr(movie, "code", None),
        topic_chat_id=getattr(movie, "source_chat_id", None),
        topic_id=getattr(movie, "source_topic_id", None),
    )


async def process_generating_job(
    db: AsyncSession,
    job: SmmClipJobModel,
    cfg: SmmSettingsModel,
    tg_client: Any,
    storage_chat_id: int | str,
    uploads_dir: str = "uploads/smm",
) -> SmmClipJobModel:
    """Fetch Storage video message, render 9:16 clip, and move job to waiting_approval/scheduled."""
    display_code, imdb_rating, genres, storage_msg_id = await _resolve_job_media(db, job)
    if not storage_msg_id:
        job.status = "failed"
        await db.flush()
        return job

    bot_handle = cfg.bot_username or os.getenv("BOT_USERNAME", "@MediaPlusOfficialBot")
    out_file = os.path.join(uploads_dir, f"clip_{job.id}.mp4")

    async def _on_progress(pct: int, stage: str) -> None:
        job.progress_pct = pct
        job.progress_stage = stage
        await db.flush()
        try:
            await db.commit()
        except Exception:
            pass

    try:
        scene_meta = await _resolve_scene_meta(db, job) if job.start_sec <= 0 else {}
        poster_url = await _resolve_media_poster_url(db, job)
        storage_msg = await tg_client.get_messages(storage_chat_id, ids=storage_msg_id)
        mode = (getattr(job, "clip_mode", "scene") or "scene").strip().lower()
        meta: Optional[dict[str, Any]] = None
        if mode in RUBRIC_MODES or mode == "facts":
            try:
                import tempfile
                m_row = (await db.execute(select(MovieModel).where(MovieModel.id == job.media_id))).scalar_one_or_none() if job.media_id else None
                poster_b = await _fetch_poster_bytes(poster_url)
                backdrop_b = await _fetch_poster_bytes(getattr(m_row, "backdrop_url", None)) if m_row else None
                low_ram = os.getenv("SMM_HD_ENABLED", "").strip().lower() not in {"1", "true", "yes", "on"}
                await _on_progress(25, f"{mode.upper()} rubrika videosi tayyorlanmoqda...")
                with tempfile.TemporaryDirectory() as r_td:
                    chunk_p = os.path.join(r_td, "chunk.mp4")
                    _, full_dur = await download_sparse_clip_source(
                        tg_client, storage_msg, chunk_p,
                        target_ratio=0.35,
                        chunk_mb=int(os.getenv("SMM_RUBRIC_CHUNK_MB", "0")) or None,
                        clip_duration=90.0,
                    )
                    sparse_s = (full_dur * 0.35) if full_dur > 120.0 else None
                    meta = await create_rubric_smm_clip(
                        video_path=chunk_p,
                        output_path=out_file,
                        rubric="bilasizmi" if mode == "facts" else mode,
                        title=job.title,
                        year=getattr(m_row, "release_year", None) if m_row else None,
                        imdb_rating=imdb_rating,
                        movie_code=display_code,
                        description=getattr(m_row, "description", None) if m_row else None,
                        genres=genres,
                        poster_bytes=poster_b,
                        backdrop_bytes=backdrop_b,
                        low_ram=low_ram,
                        sample_start_sec=sparse_s,
                        sample_span_sec=80.0 if sparse_s is not None else None,
                    )
            except Exception as rubric_exc:
                logger.warning("Rubric render fallback to scene for job #%s (%s): %s", job.id, mode, rubric_exc)
                job.clip_mode = "scene"
                meta = None
        if meta is None:
            meta = await create_smart_smm_clip(
                client=tg_client, storage_msg=storage_msg, output_path=out_file,
                movie_code=display_code, imdb_rating=imdb_rating,
                duration_sec=job.duration_sec or cfg.clip_duration_sec,
                start_sec=job.start_sec if job.start_sec > 0 else None,
                copyright_shield=cfg.copyright_shield,
                bot_username=bot_handle,
                progress_cb=_on_progress,
                poster_url=poster_url,
                hook_text=getattr(job, "hook_text", None),
                genres=genres,
                **scene_meta,
            )
    except Exception as exc:
        logger.warning("SMM clip generation failed for job #%s (%s): %s", job.id, job.movie_code, exc)
        job.status = "failed"
        job.progress_stage = "Xatolik yuz berdi"
        await db.flush()
        await db.refresh(job)
        return job

    job.start_sec = float(meta.get("start_sec") or 0.0)
    job.duration_sec = float(meta.get("duration_sec") or job.duration_sec or cfg.clip_duration_sec or 28.0)
    job.hook_text = meta.get("hook_text") or getattr(job, "hook_text", None)
    job.clip_path = f"uploads/smm/clip_{job.id}.mp4"

    # Backup generated clip to Telegram Storage (prefer BOT_TOKEN since SMM userbot may be read-only member)
    if storage_chat_id and os.path.exists(out_file):
        try:
            bot_token = os.getenv("BOT_TOKEN", "").strip()
            cap_storage = f"🎬 SMM Clip #{job.id} (#{display_code})"
            if bot_token:
                ok_up, msg_id_str, _ = await _post_telegram_video(
                    bot_token=bot_token,
                    chat_id=str(storage_chat_id),
                    video_path=out_file,
                    caption=cap_storage,
                )
                if ok_up and msg_id_str and msg_id_str.isdigit():
                    job.clip_storage_message_id = int(msg_id_str)
            if not job.clip_storage_message_id and tg_client and hasattr(tg_client, "send_file"):
                sent = await tg_client.send_file(
                    storage_chat_id,
                    out_file,
                    caption=cap_storage,
                    supports_streaming=True,
                )
                sent_id = getattr(sent, "id", None)
                if isinstance(sent_id, int) and sent_id > 0:
                    job.clip_storage_message_id = sent_id
        except Exception as exc:
            logger.warning("SMM clip storage backup skipped for job #%s: %s", job.id, exc)

    job.caption = job.caption or build_movie_caption(
        movie_code=display_code, imdb_rating=imdb_rating,
        genres=genres, bot_username=bot_handle,
        hook_text=getattr(job, "hook_text", None),
    )
    job.status = "scheduled" if cfg.mode == "FULL_AUTO" else "waiting_approval"
    job.progress_pct = 100
    job.progress_stage = "Nashr navbatida (Avto)" if cfg.mode == "FULL_AUTO" else "Tasdiq kutmoqda"
    await db.flush()
    await db.refresh(job)

    try:
        await send_admin_smm_preview(
            job_id=job.id,
            title=job.title,
            movie_code=display_code,
            mode=cfg.mode,
            video_path=out_file,
            caption=job.caption or "",
            admin_telegram_id=getattr(cfg, "admin_telegram_id", None),
            start_sec=job.start_sec,
        )
    except Exception as exc:
        logger.warning("SMM admin Telegram preview skipped for job #%s: %s", job.id, exc)
    return job


async def process_publish_job(
    db: AsyncSession,
    job: SmmClipJobModel,
    cfg: SmmSettingsModel,
    dispatcher: Optional[MultiPlatformDispatcher] = None,
    base_public_url: str = "",
    tg_client: Any = None,
    storage_chat_id: int | str = 0,
) -> SmmClipJobModel:
    """Publish rendered clip across enabled platforms and save per-platform results."""
    bot_handle = cfg.bot_username or os.getenv("BOT_USERNAME", "@MediaPlusOfficialBot")
    display_code, _, _, _ = await _resolve_job_media(db, job)

    target_path = (job.clip_path or f"uploads/smm/clip_{job.id}.mp4").strip()
    if not os.path.exists(target_path) and getattr(job, "clip_storage_message_id", None) and tg_client and storage_chat_id:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
            msg = await tg_client.get_messages(storage_chat_id, ids=int(job.clip_storage_message_id))
            if msg and getattr(msg, "media", None):
                tmp_path = f"{target_path}.tmp.{uuid.uuid4().hex}"
                await tg_client.download_media(msg, file=tmp_path)
                if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                    os.replace(tmp_path, target_path)
        except Exception as exc:
            logger.warning("SMM clip restore before publish failed for job #%s: %s", job.id, exc)

    if not dispatcher:
        dispatcher = MultiPlatformDispatcher()
        if cfg.telegram_channel_id:
            dispatcher.publishers["telegram"] = TelegramChannelPublisher(
                channel_id=cfg.telegram_channel_id, bot_username=bot_handle
            )

    video_url = f"{base_public_url.rstrip('/')}/api/v1/smm/jobs/{job.id}/video" if base_public_url and job.id else ""
    status_map = dict(job.platforms_status or {})
    pending_platforms = [
        p for p in (cfg.enabled_platforms or [])
        if status_map.get(p, {}).get("status") != "published"
    ]
    if pending_platforms:
        results = await dispatcher.publish_all(
            video_path=target_path, caption=job.caption or "",
            movie_code=display_code, platforms=pending_platforms, video_url=video_url,
            bot_username=bot_handle, hook_text=getattr(job, "hook_text", None) or "",
        )
        for plat, res in results.items():
            status_map[plat] = {"enabled": True, "status": "published" if res.success else "failed", "post_id": res.post_id, "error": res.error}
            if not res.success:
                await send_admin_alert(
                    f"pub_err:{plat}",
                    f"⚠️ <b>SMM Nashr Xatosi ({plat})</b>\n🎬 Job #{job.id} (#{display_code})\n❌ {res.error or 'Noma’lum xato'}\n\n<i>Token muddati tugagan bo‘lsa Render env dan yangilang.</i>",
                    admin_telegram_id=getattr(cfg, "admin_telegram_id", None),
                )

    any_ok = any(st.get("status") == "published" for st in status_map.values() if isinstance(st, dict))
    job.platforms_status = status_map
    job.status = "completed" if any_ok else "failed"
    job.progress_pct = 100
    job.progress_stage = "Nashr qilindi" if any_ok else "Nashrda xatolik"
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

    now_local = datetime.now(TASHKENT_TZ)
    day_start_utc = now_local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    month_start_utc = now_local.replace(day=1, hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    monthly_limit = max(1, int(os.getenv("SMM_MONTHLY_LIMIT", "90")))
    daily_limit = max(1, int(cfg.daily_limit or 3))

    daily_cnt = (await db.execute(select(func.count()).select_from(SmmClipJobModel).where(SmmClipJobModel.status == "completed", SmmClipJobModel.updated_at >= day_start_utc))).scalar() or 0
    monthly_cnt = (await db.execute(select(func.count()).select_from(SmmClipJobModel).where(SmmClipJobModel.status == "completed", SmmClipJobModel.updated_at >= month_start_utc))).scalar() or 0

    generated, published = 0, 0
    gen_job = (
        await db.execute(
            select(SmmClipJobModel)
            .where(SmmClipJobModel.status == "generating")
            .order_by(case((SmmClipJobModel.clip_mode != "scene", 0), else_=1), SmmClipJobModel.id.asc())
            .limit(1)
        )
    ).scalar_one_or_none()
    if (
        not gen_job
        and getattr(cfg, "auto_pick_from_catalog", False)
        and int(daily_cnt) < daily_limit
        and int(monthly_cnt) < monthly_limit
        and tg_client
        and storage_chat_id
    ):
        buffered = (
            await db.execute(
                select(func.count())
                .select_from(SmmClipJobModel)
                .where(SmmClipJobModel.status.in_(("waiting_approval", "scheduled", "publishing")))
            )
        ).scalar() or 0
        if int(buffered) == 0:
            gen_job = await auto_pick_catalog_movie(db, now_local=now_local)
    if gen_job and tg_client and storage_chat_id:
        updated_gen = await process_generating_job(db, gen_job, cfg, tg_client, storage_chat_id)
        if updated_gen.status != "failed":
            generated = 1

    pub_job = (await db.execute(select(SmmClipJobModel).where(SmmClipJobModel.status == "publishing").order_by(SmmClipJobModel.id.asc()).limit(1))).scalar_one_or_none()
    if not pub_job:
        now_utc = datetime.now(timezone.utc)
        pub_job = (
            await db.execute(
                select(SmmClipJobModel)
                .where(
                    SmmClipJobModel.status == "scheduled",
                    SmmClipJobModel.scheduled_at.isnot(None),
                    SmmClipJobModel.scheduled_at <= now_utc,
                )
                .order_by(SmmClipJobModel.id.asc())
                .limit(1)
            )
        ).scalar_one_or_none()
    if not pub_job and cfg.mode == "FULL_AUTO":
        last_pub = (await db.execute(select(func.max(SmmClipJobModel.updated_at)).where(SmmClipJobModel.status == "completed"))).scalar()
        if is_schedule_due(
            cfg.schedule_hours,
            now_local,
            last_pub,
            int(daily_cnt),
            daily_limit,
            monthly_count=int(monthly_cnt),
            monthly_limit=monthly_limit,
        ):
            pub_job = (await db.execute(select(SmmClipJobModel).where(SmmClipJobModel.status == "scheduled").order_by(SmmClipJobModel.id.asc()).limit(1))).scalar_one_or_none()

    if pub_job:
        await process_publish_job(
            db,
            pub_job,
            cfg,
            base_public_url=base_public_url,
            tg_client=tg_client,
            storage_chat_id=storage_chat_id,
        )
        published = 1

    if generated == 0 and published == 0 and os.getenv("POSTER_BACKFILL_ENABLED", "1").strip().lower() in {"1", "true", "yes", "on"}:
        try:
            from app.api.v1.posters import backfill_one_unlocalized_poster

            bf_res = await backfill_one_unlocalized_poster(db)
            if bf_res.get("localized"):
                logger.info("Idle poster backfill localized: %s#%s", bf_res.get("media_type"), bf_res.get("media_id"))
        except Exception as bf_exc:
            logger.warning("Idle poster backfill skipped: %s", bf_exc)
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


def compute_worker_sleep_seconds(interval: int, last_result: Optional[dict]) -> int:
    """Short-circuit the 180s idle poll sleep to 10s when queued jobs are actively rendering or publishing."""
    if last_result and (int(last_result.get("generated") or 0) > 0 or int(last_result.get("published") or 0) > 0):
        return min(int(interval), 10)
    return int(interval)


async def supervised_run_smm_worker() -> None:
    """Long-running background supervisor for Cycle 2 SMM rendering and publishing."""
    interval = max(30, int(os.getenv("SMM_WORKER_INTERVAL_SEC", "180")))
    default_delay = "25" if (os.getenv("RENDER_EXTERNAL_URL") or os.getenv("RENDER")) else "0"
    startup_delay = max(0, int(os.getenv("SMM_STARTUP_DELAY_SEC", default_delay)))
    tg_client = None
    session_disabled = False
    _WORKER_STATE["running"] = True
    _WORKER_STATE["started_at"] = datetime.now(timezone.utc).isoformat()
    logger.info(
        "SMM worker started: enabled=%s has_smm_session=%s has_api_id=%s has_storage_id=%s interval=%ss startup_delay=%ss",
        os.getenv("SMM_AUTOPILOT_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"},
        bool(resolve_smm_session_string()),
        os.getenv("TELEGRAM_API_ID", "").strip().isdigit(),
        bool(os.getenv("STORAGE_CHANNEL_ID", "").strip()),
        interval,
        startup_delay,
    )
    if startup_delay > 0:
        await asyncio.sleep(startup_delay)

    while True:
        res: Optional[dict] = None
        try:
            _WORKER_STATE["last_tick_at"] = datetime.now(timezone.utc).isoformat()
            enabled = os.getenv("SMM_AUTOPILOT_ENABLED", "").strip().lower() in {"1", "true", "yes", "on"}
            if enabled:
                sess = "" if session_disabled else resolve_smm_session_string()
                api_id = os.getenv("TELEGRAM_API_ID", "").strip()
                api_hash = os.getenv("TELEGRAM_API_HASH", "").strip()
                if sess and api_id.isdigit() and api_hash and tg_client is None:
                    try:
                        from telethon import TelegramClient
                        from telethon.sessions import StringSession

                        candidate = TelegramClient(StringSession(sess), int(api_id), api_hash)
                        await asyncio.wait_for(candidate.connect(), timeout=20.0)
                        tg_client = candidate
                    except (KeyboardInterrupt, asyncio.CancelledError):
                        raise
                    except Exception as tg_exc:
                        tg_client = None
                        if "AuthKeyDuplicated" in type(tg_exc).__name__ or "AuthKeyDuplicated" in str(tg_exc):
                            session_disabled = True
                            await send_admin_alert(
                                "smm_session_dead",
                                f"🚨 <b>SMM Telegram Sessiya Uzildi</b>\n❌ {type(tg_exc).__name__}: {tg_exc}\n\n<i>SMM_TELEGRAM_STRING_SESSION ni yangilab Render ga qo‘ying.</i>",
                            )
                        _WORKER_STATE["last_error"] = f"Telethon connect: {tg_exc}"
                        logger.warning("SMM Telethon connect error (publish still active): %s", tg_exc)
                res = await run_smm_worker_cycle(tg_client=tg_client)
                _WORKER_STATE["last_result"] = res
                _WORKER_STATE["last_error"] = None
                if res.get("generated") or res.get("published"):
                    logger.info("SMM worker cycle: %s", res)
        except (KeyboardInterrupt, asyncio.CancelledError):
            _WORKER_STATE["running"] = False
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
                await send_admin_alert(
                    "smm_session_dead",
                    f"🚨 <b>SMM Telegram Sessiya Uzildi</b>\n❌ {exc}\n\n<i>SMM_TELEGRAM_STRING_SESSION ni yangilab Render ga qo‘ying.</i>",
                )
            else:
                await send_admin_alert("smm_worker_err", f"⚠️ <b>SMM Worker Xatosi</b>\n❌ {type(exc).__name__}: {exc}")
            _WORKER_STATE["last_error"] = str(exc)
            logger.warning("SMM worker tick error (API/Bot isolated): %s", exc)
        await asyncio.sleep(compute_worker_sleep_seconds(interval, res))
