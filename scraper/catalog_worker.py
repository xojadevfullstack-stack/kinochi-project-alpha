"""Render-safe Forward-Only Catalog Autopilot Worker (Hybrid Architecture)."""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import func, select

from scraper.duplicate_checker import DuplicateChecker
from scraper.queue_manager import QueueManager
from scraper.telethon_moderator_pipeline import TelethonModeratorPipeline

logger = logging.getLogger(__name__)
FORWARD_ONLY_SOURCES: tuple[str, ...] = ("uzmovi", "asilmedia")
TASHKENT_TZ = timezone(timedelta(hours=5))
_WORKER_STATE: dict[str, Any] = {
    "running": False,
    "started_at": None,
    "last_tick_at": None,
    "last_error": None,
    "last_result": None,
}


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    return default if raw is None or not str(raw).strip() else str(raw).strip().lower() in {"1", "true", "yes", "on"}


def is_render_catalog_enabled() -> bool:
    """Return True when hybrid forward-only catalog autopilot is enabled."""
    explicit = os.getenv("RENDER_CATALOG_ENABLED")
    if explicit is not None and str(explicit).strip():
        return _env_flag("RENDER_CATALOG_ENABLED", False)
    return _env_flag("SCRAPER_ENABLED", False) and _env_flag("AUTO_CONTENT_ENABLED", False)


def _resolve_catalog_session_string() -> str:
    """Resolve dedicated catalog Telethon string session without reusing SMM session."""
    return (os.getenv("CATALOG_TELEGRAM_STRING_SESSION") or os.getenv("TELEGRAM_STRING_SESSION") or "").strip()


def get_catalog_worker_state() -> dict[str, Any]:
    """Return non-secret Render forward-only catalog worker runtime diagnostics."""
    cat_sess = _resolve_catalog_session_string()
    smm_sess = os.getenv("SMM_TELEGRAM_STRING_SESSION", "").strip()
    return {
        "enabled": is_render_catalog_enabled(),
        "has_catalog_session": bool(cat_sess),
        "session_collision": bool(cat_sess and smm_sess and cat_sess == smm_sess),
        "has_api_creds": os.getenv("TELEGRAM_API_ID", "").strip().isdigit() and bool(os.getenv("TELEGRAM_API_HASH", "").strip()),
        "daily_limit": max(1, int(os.getenv("RENDER_CATALOG_DAILY_LIMIT", "4"))),
        **dict(_WORKER_STATE),
    }


def _build_telethon_client() -> Any:
    """Create an unconnected TelethonClient using the catalog StringSession."""
    from telethon import TelegramClient
    from telethon.sessions import StringSession

    return TelegramClient(
        StringSession(_resolve_catalog_session_string()),
        int(os.getenv("TELEGRAM_API_ID", "0").strip()),
        os.getenv("TELEGRAM_API_HASH", "").strip(),
    )


async def _count_today_forward_published(session_factory: Any = None) -> int:
    """Count ingest_items published today (Tashkent UTC+5) from forwardable sources."""
    from app.infrastructure.db.models.ingest_item import IngestItemModel

    if session_factory is None:
        from app.infrastructure.db.session import async_session_factory
        session_factory = async_session_factory
    day_start_utc = datetime.now(TASHKENT_TZ).replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)
    async with session_factory() as db:
        stmt = select(func.count(IngestItemModel.id)).where(
            IngestItemModel.status == "published",
            IngestItemModel.source.in_(FORWARD_ONLY_SOURCES),
            IngestItemModel.updated_at >= day_start_utc,
        )
        return int((await db.execute(stmt)).scalar() or 0)


async def _refresh_forward_queues_if_empty(qm: QueueManager) -> int:
    """Parse page 1 of forward-only sources when queue is exhausted."""
    from scraper.site_parser import parse_asilmedia_page_async, parse_uzmovi_page_async

    added_total = 0
    for src, parser_fn in (("uzmovi", parse_uzmovi_page_async), ("asilmedia", parse_asilmedia_page_async)):
        try:
            items = await parser_fn(page=1)
            if items:
                added_total += int(await qm.add_items_batch_async(items[:10]))
        except Exception as exc:
            logger.warning("Render catalog page-1 parse failed (%s): %s", src, exc)
    return added_total


async def _claim_forward_item(qm: QueueManager, worker_id: str = "render_forward") -> Any:
    """Claim one queued item strictly from FORWARD_ONLY_SOURCES (never kinochilar)."""
    offset = datetime.now(TASHKENT_TZ).hour % len(FORWARD_ONLY_SOURCES)
    for src in FORWARD_ONLY_SOURCES[offset:] + FORWARD_ONLY_SOURCES[:offset]:
        item = await qm.claim_next_async(worker_id=worker_id, source=src)
        if item is not None:
            return item
    return None


async def run_catalog_worker_tick(session_factory: Any = None) -> dict[str, Any]:
    """Run one Render-safe forward-only catalog tick (at most 1 item, copy_only=True)."""
    if not is_render_catalog_enabled():
        return {"processed": 0, "skipped": "disabled"}

    cat_sess = _resolve_catalog_session_string()
    if not cat_sess:
        return {"processed": 0, "skipped": "no_session"}
    smm_sess = os.getenv("SMM_TELEGRAM_STRING_SESSION", "").strip()
    if smm_sess and cat_sess == smm_sess:
        logger.error("Catalog session matches SMM_TELEGRAM_STRING_SESSION; refusing start.")
        return {"processed": 0, "skipped": "session_collision"}
    if not os.getenv("TELEGRAM_API_ID", "").strip().isdigit() or not os.getenv("TELEGRAM_API_HASH", "").strip():
        return {"processed": 0, "skipped": "missing_api_creds"}

    daily_limit = max(1, int(os.getenv("RENDER_CATALOG_DAILY_LIMIT", "4")))
    published_today = await _count_today_forward_published(session_factory=session_factory)
    if published_today >= daily_limit:
        return {"processed": 0, "skipped": "daily_limit", "published_today": published_today, "daily_limit": daily_limit}

    qm = QueueManager()
    await qm.recover_stale_in_progress_async(max_age_seconds=1800)
    item = await _claim_forward_item(qm)
    if item is None:
        await _refresh_forward_queues_if_empty(qm)
        item = await _claim_forward_item(qm)
    if item is None:
        return {"processed": 0, "skipped": "empty_queue"}
    if getattr(item, "source", None) not in FORWARD_ONLY_SOURCES:
        await qm.update_status_async(item.id, "queued", error_message="Forward-only guard rejected non-forward source")
        return {"processed": 0, "skipped": "unsupported_source"}

    tg_client = _build_telethon_client()
    try:
        await tg_client.connect()
        if not await tg_client.is_user_authorized():
            await qm.update_status_async(item.id, "queued", error_message="Render catalog Telethon session unauthorized")
            return {"processed": 0, "skipped": "unauthorized"}

        dup_checker = DuplicateChecker()
        await dup_checker.refresh_cache()
        pipeline = TelethonModeratorPipeline(client=tg_client, duplicate_checker=dup_checker, copy_only=True)
        ok = await pipeline.run_item(item)
        return {"processed": 1, "published": int(bool(ok)), "source": getattr(item, "source", None), "item_id": str(getattr(item, "id", ""))}
    except Exception as exc:
        logger.warning("Render catalog worker item failed (%s): %s", getattr(item, "id", "?"), exc)
        try:
            await qm.update_status_async(item.id, "failed", error_message=str(exc)[:400])
        except Exception:
            pass
        return {"processed": 0, "error": str(exc)}
    finally:
        try:
            await tg_client.disconnect()
        except Exception as disc_err:
            logger.debug("Catalog Telethon disconnect error: %s", disc_err)


async def supervised_run_catalog_worker() -> None:
    """Long-running background supervisor for Render forward-only catalog growth."""
    interval = max(120, int(os.getenv("CATALOG_WORKER_INTERVAL_SEC", "3600")))
    default_delay = "50" if (os.getenv("RENDER_EXTERNAL_URL") or os.getenv("RENDER")) else "0"
    startup_delay = max(0, int(os.getenv("CATALOG_STARTUP_DELAY_SEC", default_delay)))
    _WORKER_STATE["running"] = True
    _WORKER_STATE["started_at"] = datetime.now(timezone.utc).isoformat()
    logger.info(
        "Render catalog worker started: enabled=%s has_session=%s interval=%ss startup_delay=%ss",
        is_render_catalog_enabled(),
        bool(_resolve_catalog_session_string()),
        interval,
        startup_delay,
    )
    if startup_delay:
        await asyncio.sleep(startup_delay)
    while True:
        try:
            res = await run_catalog_worker_tick()
            _WORKER_STATE["last_tick_at"] = datetime.now(timezone.utc).isoformat()
            _WORKER_STATE["last_result"] = res
            _WORKER_STATE["last_error"] = None
            logger.info("Render catalog tick: %s", res)
        except Exception as exc:
            _WORKER_STATE["last_tick_at"] = datetime.now(timezone.utc).isoformat()
            _WORKER_STATE["last_error"] = str(exc)
            logger.exception("Render catalog worker tick failed: %s", exc)
        await asyncio.sleep(interval)