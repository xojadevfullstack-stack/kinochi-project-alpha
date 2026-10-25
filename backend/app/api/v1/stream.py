import os
import re
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Header
from fastapi.responses import StreamingResponse, JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db_session
from app.infrastructure.db.models import MovieModel, EpisodeModel, SeriesModel
from app.api.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stream", tags=["stream"])


def parse_byte_range(range_header: str, file_size: int) -> tuple[int, int]:
    """Parse HTTP Range header: 'bytes=start-end'."""
    range_match = re.match(r"bytes=(\d+)-(\d*)", range_header)
    if not range_match:
        return 0, file_size - 1

    start = int(range_match.group(1))
    end_str = range_match.group(2)
    end = int(end_str) if end_str else file_size - 1

    if start >= file_size:
        raise HTTPException(
            status_code=status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE,
            detail="Range out of bounds"
        )

    end = min(end, file_size - 1)
    return start, end


def stream_file_chunk(file_path: str, start: int, end: int, chunk_size: int = 1024 * 512):
    """Generator to yield file chunks within [start, end]."""
    with open(file_path, "rb") as f:
        f.seek(start)
        remaining = end - start + 1
        while remaining > 0:
            read_size = min(chunk_size, remaining)
            data = f.read(read_size)
            if not data:
                break
            remaining -= len(data)
            yield data


@router.get("/movie/{code}")
@limiter.limit("120/minute")
async def resolve_movie_stream(
    request: Request,
    code: str,
    lang: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Resolve video stream metadata, available audio sources, and fallback links for a movie.
    """
    stmt = select(MovieModel).where(MovieModel.code == code)
    res = await db.execute(stmt)
    movie = res.scalars().first()

    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")

    translations = movie.translations or []
    
    # Check if local video file exists in uploads/
    local_video_path = None
    possible_local_paths = [
        os.path.join("uploads", "movies", f"{code}.mp4"),
        os.path.join("uploads", f"{code}.mp4"),
    ]
    for p in possible_local_paths:
        if os.path.exists(p):
            local_video_path = p
            break

    # Determine active language translation
    selected_tr = None
    if lang:
        selected_tr = next((t for t in translations if t.get("language") == lang), None)
    if not selected_tr and translations:
        selected_tr = translations[0]

    stream_url = None
    stream_type = "fallback"

    if local_video_path:
        stream_url = f"/api/v1/stream/play/movie/{code}"
        stream_type = "direct_mp4"
    elif selected_tr and selected_tr.get("telegram_file_id"):
        stream_url = f"/api/v1/stream/play/movie/{code}?lang={encodeURIComponent(selected_tr.get('language', 'O\'zbekcha'))}"
        stream_type = "telegram_proxy"

    return {
        "media_type": "movie",
        "code": movie.code,
        "title": movie.title,
        "active_language": selected_tr.get("language") if selected_tr else "O'zbekcha",
        "stream_url": stream_url,
        "stream_type": stream_type,
        "trailer_url": movie.trailer_url,
        "translations": [
            {
                "id": idx + 1,
                "language": tr.get("language", "O'zbekcha"),
                "has_video": bool(tr.get("telegram_file_id") or tr.get("storage_channel_message_id")),
                "storage_channel_message_id": tr.get("storage_channel_message_id"),
            }
            for idx, tr in enumerate(translations)
        ],
        "telegram_deep_link": f"https://t.me/kinochi_uz_bot?start={movie.code}",
    }


@router.get("/episode/{code}")
@limiter.limit("120/minute")
async def resolve_episode_stream(
    request: Request,
    code: str,
    lang: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Resolve video stream metadata, available audio sources, and fallback links for an episode.
    """
    stmt = select(EpisodeModel).where(EpisodeModel.code == code)
    res = await db.execute(stmt)
    episode = res.scalars().first()

    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")

    translations = episode.translations or []
    
    local_video_path = None
    possible_local_paths = [
        os.path.join("uploads", "episodes", f"{code}.mp4"),
        os.path.join("uploads", f"{code}.mp4"),
    ]
    for p in possible_local_paths:
        if os.path.exists(p):
            local_video_path = p
            break

    selected_tr = None
    if lang:
        selected_tr = next((t for t in translations if t.get("language") == lang), None)
    if not selected_tr and translations:
        selected_tr = translations[0]

    stream_url = None
    stream_type = "fallback"

    if local_video_path:
        stream_url = f"/api/v1/stream/play/episode/{code}"
        stream_type = "direct_mp4"
    elif selected_tr and selected_tr.get("telegram_file_id"):
        stream_url = f"/api/v1/stream/play/episode/{code}"
        stream_type = "telegram_proxy"

    return {
        "media_type": "episode",
        "code": episode.code,
        "title": episode.title,
        "episode_number": episode.episode_number,
        "active_language": selected_tr.get("language") if selected_tr else "O'zbekcha",
        "stream_url": stream_url,
        "stream_type": stream_type,
        "translations": [
            {
                "id": idx + 1,
                "language": tr.get("language", "O'zbekcha"),
                "has_video": bool(tr.get("telegram_file_id") or tr.get("storage_channel_message_id")),
                "storage_channel_message_id": tr.get("storage_channel_message_id"),
            }
            for idx, tr in enumerate(translations)
        ],
        "telegram_deep_link": f"https://t.me/kinochi_uz_bot?start={episode.code}",
    }


@router.get("/play/{media_type}/{code}")
async def play_video_stream(
    media_type: str,
    code: str,
    request: Request,
    range: Optional[str] = Header(None)
):
    """
    HTTP 206 Partial Content video streamer for browser <video> player with Seek support.
    """
    possible_paths = [
        os.path.join("uploads", f"{media_type}s", f"{code}.mp4"),
        os.path.join("uploads", f"{code}.mp4"),
    ]
    
    file_path = None
    for p in possible_paths:
        if os.path.exists(p):
            file_path = p
            break

    if not file_path:
        # File not on local storage
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Video stream fayli topilmadi yoki hali yuklanmagan"
        )

    file_size = os.path.getsize(file_path)

    if range:
        start, end = parse_byte_range(range, file_size)
        content_length = end - start + 1
        headers = {
            "Content-Range": f"bytes {start}-{end}/{file_size}",
            "Accept-Ranges": "bytes",
            "Content-Length": str(content_length),
            "Content-Type": "video/mp4",
        }
        return StreamingResponse(
            stream_file_chunk(file_path, start, end),
            status_code=status.HTTP_206_PARTIAL_CONTENT,
            headers=headers,
            media_type="video/mp4"
        )
    else:
        # Full file stream
        headers = {
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
            "Content-Type": "video/mp4",
        }
        return StreamingResponse(
            stream_file_chunk(file_path, 0, file_size - 1),
            status_code=status.HTTP_200_OK,
            headers=headers,
            media_type="video/mp4"
        )


def encodeURIComponent(s: str) -> str:
    import urllib.parse
    return urllib.parse.quote(s)
