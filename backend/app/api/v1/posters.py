"""Telegram poster storage (channel + forum topic) and public proxy endpoints."""

import html
import logging
import os
import re
from typing import Any, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response

from app.api.deps import get_current_admin
from app.api.limiter import limiter
from app.core.config import settings
from app.infrastructure.telegram.telegram_client import telegram_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/posters", tags=["posters"])

_VALID_FILE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{20,160}$")
_DEFAULT_PUBLIC_API_BASE = "https://kinochi-project-alpha-9g6j.onrender.com"
_BACKFILL_SKIP_CACHE: set[str] = set()
_BACKFILL_SKIP_TTL_SEC = 7 * 86400


def build_telegram_poster_url(file_id: str) -> str:
    """Build a permanent public backend proxy URL for a Telegram-stored poster."""
    base = (
        os.getenv("PUBLIC_API_BASE_URL")
        or os.getenv("RENDER_EXTERNAL_URL")
        or _DEFAULT_PUBLIC_API_BASE
    ).strip().rstrip("/")
    return f"{base}/api/v1/posters/tg/{file_id}"


async def upload_poster_to_telegram(
    photo_bytes: bytes,
    title: str,
    code: Optional[str] = None,
    topic_chat_id: Optional[int | str] = None,
    topic_id: Optional[int] = None,
) -> Optional[str]:
    """Save localized poster in STORAGE_CHANNEL_ID and (if linked) into the media's forum topic."""
    if not photo_bytes:
        return None

    safe_title = html.escape(title or "Poster")
    code_line = f"\n🔑 Kod: <code>{html.escape(str(code))}</code>" if code else ""
    caption = f"🖼 <b>{safe_title}</b> (O'zbekcha poster){code_line}"

    storage_id = settings.STORAGE_CHANNEL_ID
    res = await telegram_client.send_photo_with_result(
        chat_id=storage_id,
        photo_bytes=photo_bytes,
        filename="uzbek_poster.jpg",
        caption=caption,
        parse_mode="HTML",
    )
    if not res.success or not res.file_id:
        logger.warning("Failed to upload localized poster to STORAGE_CHANNEL_ID (%s): %s", storage_id, res.error)
        return None

    target_topic_chat = topic_chat_id or settings.AUTO_TOPIC_CHAT_ID
    if topic_id and target_topic_chat:
        try:
            topic_res = await telegram_client.send_photo_with_result(
                chat_id=target_topic_chat,
                photo_bytes=photo_bytes,
                filename="uzbek_poster.jpg",
                caption=caption,
                parse_mode="HTML",
                message_thread_id=int(topic_id),
            )
            if not topic_res.success:
                logger.warning(
                    "Poster uploaded to channel but topic mirror failed (chat=%s topic=%s): %s",
                    target_topic_chat,
                    topic_id,
                    topic_res.error,
                )
        except Exception as exc:
            logger.warning("Topic poster mirror exception (chat=%s topic=%s): %s", target_topic_chat, topic_id, exc)

    return build_telegram_poster_url(res.file_id)


@router.get("/tg/{file_id}")
@limiter.limit("300/minute")
async def get_telegram_poster(request: Request, file_id: str) -> Response:
    """Stream a Telegram-stored poster publicly without exposing BOT_TOKEN."""
    if not _VALID_FILE_ID_RE.match(file_id):
        raise HTTPException(status_code=400, detail="Noto'g'ri Telegram file_id formati")

    result = await telegram_client.download_file_bytes(file_id)
    if not result:
        raise HTTPException(status_code=404, detail="Poster topilmadi")

    content, mime_type = result
    return Response(
        content=content,
        media_type=mime_type,
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


def should_localize_poster(tmdb_id: Optional[int], poster_url: Optional[str]) -> bool:
    """Return True when media has a TMDb ID or external poster_url not yet stored on /posters/tg/."""
    clean_url = (poster_url or "").strip()
    if "/api/v1/posters/tg/" in clean_url:
        return False
    return bool((tmdb_id and int(tmdb_id) > 0) or clean_url.startswith(("http://", "https://")))


async def run_poster_localization_task(
    media_type: Literal["movie", "series"],
    media_id: int,
    allow_in_testing: bool = False,
) -> Optional[str]:
    """Background task: localize movie/series poster to Uzbek, save in Telegram, update DB."""
    if os.getenv("APP_ENV") == "testing" and not allow_in_testing:
        return None
    try:
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        from app.core.cache import delete_cache_pattern
        from app.infrastructure.db.models.movie import MovieModel
        from app.infrastructure.db.models.series import SeriesModel
        from app.infrastructure.db.session import async_session_factory
        from app.infrastructure.external.poster_localizer import localize_poster_and_upload

        async with async_session_factory() as db:
            if media_type == "movie":
                stmt = select(MovieModel).where(MovieModel.id == media_id)
                obj = (await db.execute(stmt)).scalar_one_or_none()
                if not obj:
                    return None
                topic_chat_id = getattr(obj, "source_chat_id", None)
                topic_id = getattr(obj, "source_topic_id", None)
                code = getattr(obj, "code", None)
            else:
                stmt = select(SeriesModel).options(selectinload(SeriesModel.source)).where(SeriesModel.id == media_id)
                obj = (await db.execute(stmt)).scalar_one_or_none()
                if not obj:
                    return None
                src = getattr(obj, "source", None)
                topic_chat_id = getattr(src, "chat_id", None) if src else None
                topic_id = getattr(src, "topic_id", None) if src else None
                code = None

            new_url = await localize_poster_and_upload(
                title=obj.title,
                tmdb_id=getattr(obj, "tmdb_id", None),
                content_type="tv" if media_type == "series" else "movie",
                manual_poster_url=getattr(obj, "poster_url", None),
                code=code,
                topic_chat_id=topic_chat_id,
                topic_id=topic_id,
            )
            if new_url and new_url != obj.poster_url:
                obj.poster_url = new_url
                await db.commit()
                await delete_cache_pattern("cache:movies:*" if media_type == "movie" else "cache:series:*")
                await delete_cache_pattern("cache:search:*")
            return new_url
    except Exception as exc:
        logger.warning("Poster localization background task failed (%s #%s): %s", media_type, media_id, exc)
        return None


def schedule_poster_localization(
    background_tasks: BackgroundTasks,
    media_type: Literal["movie", "series"],
    media_id: Optional[int],
    tmdb_id: Optional[int] = None,
    poster_url: Optional[str] = None,
) -> None:
    """Schedule automatic Uzbek poster localization when TMDb ID or external poster_url is provided."""
    if not media_id or not should_localize_poster(tmdb_id=tmdb_id, poster_url=poster_url):
        return
    background_tasks.add_task(run_poster_localization_task, media_type, int(media_id))


@router.post("/localize/{media_type}/{media_id}")
@limiter.limit("20/minute")
async def localize_media_poster_now(
    request: Request,
    media_type: Literal["movie", "series"],
    media_id: int,
    admin: dict = Depends(get_current_admin),
) -> dict:
    """Admin endpoint to trigger Uzbek poster localization immediately."""
    new_url = await run_poster_localization_task(media_type, media_id, allow_in_testing=True)
    if not new_url:
        raise HTTPException(status_code=400, detail="Posterni o'zbekchalashtirib bo'lmadi (TMDb ID yoki poster_url tekshiring).")
    return {"success": True, "poster_url": new_url}


async def _is_backfill_skipped(cache_key: str) -> bool:
    if cache_key in _BACKFILL_SKIP_CACHE:
        return True
    try:
        from app.core.cache import get_cache

        val = await get_cache(cache_key)
        if val is not None:
            _BACKFILL_SKIP_CACHE.add(cache_key)
            return True
    except Exception as exc:
        logger.debug("Poster backfill skip check failed (%s): %s", cache_key, exc)
    return False


async def _mark_backfill_skipped(cache_key: str) -> None:
    _BACKFILL_SKIP_CACHE.add(cache_key)
    try:
        from app.core.cache import set_cache

        await set_cache(cache_key, "1", ttl_seconds=_BACKFILL_SKIP_TTL_SEC)
    except Exception as exc:
        logger.debug("Poster backfill skip mark failed (%s): %s", cache_key, exc)


async def backfill_one_unlocalized_poster(db: Any, allow_in_testing: bool = False) -> dict[str, Any]:
    """Safely localize 1 already-uploaded movie/series poster using v10 quality gate + 7d skip cooldown."""
    if os.getenv("APP_ENV") == "testing" and not allow_in_testing:
        return {"localized": 0, "skipped": 0}
    from sqlalchemy import or_, select
    from sqlalchemy.orm import selectinload

    from app.core.cache import delete_cache_pattern
    from app.infrastructure.db.models.movie import MovieModel
    from app.infrastructure.db.models.series import SeriesModel
    from app.infrastructure.external.poster_localizer import localize_poster_and_upload

    candidates: list[tuple[str, Any, Optional[str], Optional[int | str], Optional[int]]] = []
    movies = (
        await db.execute(
            select(MovieModel)
            .where(or_(MovieModel.poster_url.is_(None), ~MovieModel.poster_url.contains("/posters/tg/")))
            .order_by(MovieModel.id.desc())
            .limit(20)
        )
    ).scalars().all()
    for m in movies:
        if should_localize_poster(getattr(m, "tmdb_id", None), getattr(m, "poster_url", None)):
            candidates.append(("movie", m, getattr(m, "code", None), getattr(m, "source_chat_id", None), getattr(m, "source_topic_id", None)))

    series_rows = (
        await db.execute(
            select(SeriesModel)
            .options(selectinload(SeriesModel.source))
            .where(or_(SeriesModel.poster_url.is_(None), ~SeriesModel.poster_url.contains("/posters/tg/")))
            .order_by(SeriesModel.id.desc())
            .limit(20)
        )
    ).scalars().all()
    for sr in series_rows:
        if should_localize_poster(getattr(sr, "tmdb_id", None), getattr(sr, "poster_url", None)):
            src = getattr(sr, "source", None)
            candidates.append(("series", sr, None, getattr(src, "chat_id", None) if src else None, getattr(src, "topic_id", None) if src else None))

    for media_type, obj, code, topic_chat_id, topic_id in candidates:
        skip_key = f"poster:v10:skip:{media_type}:{obj.id}"
        if await _is_backfill_skipped(skip_key):
            continue
        new_url = await localize_poster_and_upload(
            title=obj.title,
            tmdb_id=getattr(obj, "tmdb_id", None),
            content_type="tv" if media_type == "series" else "movie",
            manual_poster_url=getattr(obj, "poster_url", None),
            code=code,
            topic_chat_id=topic_chat_id,
            topic_id=topic_id,
        )
        if new_url and new_url != obj.poster_url:
            obj.poster_url = new_url
            await db.flush()
            await delete_cache_pattern("cache:movies:*" if media_type == "movie" else "cache:series:*")
            await delete_cache_pattern("cache:search:*")
            return {"localized": 1, "skipped": 0, "media_type": media_type, "media_id": obj.id, "title": obj.title}
        await _mark_backfill_skipped(skip_key)
        return {"localized": 0, "skipped": 1, "media_type": media_type, "media_id": obj.id, "title": obj.title}
    return {"localized": 0, "skipped": 0}
