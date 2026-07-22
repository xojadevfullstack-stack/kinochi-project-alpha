"""API v1 — Series endpoints."""
import logging
import asyncio
import os
import tempfile
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, UploadFile, File, Form
from pydantic import BaseModel

from app.api.deps import get_series_service, get_current_admin, get_admin_or_bot
from app.application.series.series_service import SeriesService
from app.domain.series.entities import (
    Series, SeriesCreate, SeriesUpdate, PaginatedSeriesResponse,
    Season, SeasonCreate, SeasonUpdate,
    Episode, EpisodeCreate, EpisodeUpdate
)
from app.infrastructure.telegram.telegram_client import telegram_client
from app.core.job_manager import job_manager, JobStatus
from app.api.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/series", tags=["series"])


# --- SERIES ---

@router.post("", response_model=Series, status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_series(
    request: Request,
    series_in: SeriesCreate,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    """Create a new series (Admin only)."""
    create_dict = series_in.model_dump(exclude_unset=True)
    return await service.create_series(create_dict)


@router.get("", response_model=PaginatedSeriesResponse)
@limiter.limit("100/minute")
async def list_series(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    category_id: int | None = None,
    page_id: int | None = None,
    exclude_paged: bool = False,
    service: SeriesService = Depends(get_series_service)
):
    """List series (Public)."""
    items, total = await service.get_all_series(skip=skip, limit=limit, category_id=category_id, page_id=page_id, exclude_paged=exclude_paged)
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 0
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return PaginatedSeriesResponse(items=items, total=total, page=page, size=limit, pages=pages)


@router.get("/search", response_model=PaginatedSeriesResponse)
@limiter.limit("60/minute")
async def search_series(
    request: Request,
    q: str = Query(..., min_length=2),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: SeriesService = Depends(get_series_service)
):
    """Search series by title (Public)."""
    items, total = await service.search_series(title_query=q, skip=skip, limit=limit)
    
    pages = (total + limit - 1) // limit if total > 0 else 0
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return PaginatedSeriesResponse(items=items, total=total, page=page, size=limit, pages=pages)


@router.get("/by-source", response_model=Series)
@limiter.limit("120/minute")
async def get_series_by_source(
    request: Request,
    chat_id: int = Query(...),
    topic_id: int | None = Query(None),
    service: SeriesService = Depends(get_series_service)
):
    """Get series by source (chat_id and topic_id) (Public)."""
    series = await service.get_series_by_source(chat_id, topic_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series

@router.get("/{series_id}", response_model=Series)
@limiter.limit("120/minute")
async def get_series(
    request: Request,
    series_id: int,
    service: SeriesService = Depends(get_series_service)
):
    """Get series by ID (Public)."""
    series = await service.get_series_by_id(series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series


@router.put("/{series_id}", response_model=Series)
async def update_series(
    series_id: int,
    series_in: SeriesUpdate,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    """Update a series (Admin only)."""
    update_dict = series_in.model_dump(exclude_unset=True)
    series = await service.update_series(series_id, update_dict)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series


@router.delete("/{series_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_series(
    series_id: int,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    """Delete a series (Admin only)."""
    success = await service.delete_series(series_id)
    if not success:
        raise HTTPException(status_code=404, detail="Series not found")


# --- SEASONS ---

@router.post("/{series_id}/seasons", response_model=Season, status_code=status.HTTP_201_CREATED)
async def create_season(
    series_id: int,
    season_in: SeasonCreate,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    """Create a new season for a series (Admin only)."""
    if season_in.series_id != series_id:
        raise HTTPException(status_code=400, detail="Series ID mismatch")
    
    try:
        return await service.create_season(season_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{series_id}/seasons", response_model=List[Season])
@limiter.limit("120/minute")
async def list_seasons(
    request: Request,
    series_id: int,
    service: SeriesService = Depends(get_series_service)
):
    """Get all seasons for a series (Public)."""
    series = await service.get_series_by_id(series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series.seasons

@router.get("/seasons/{season_id}", response_model=Season)
@limiter.limit("120/minute")
async def get_season(
    request: Request,
    season_id: int,
    service: SeriesService = Depends(get_series_service)
):
    """Get a season by ID (Public)."""
    season = await service.get_season_by_id(season_id)
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    return season


@router.put("/seasons/{season_id}", response_model=Season)
async def update_season(
    season_id: int,
    season_in: SeasonUpdate,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    """Update a season (Admin only)."""
    season = await service.update_season(season_id, season_in)
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    return season


@router.delete("/seasons/{season_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_season(
    season_id: int,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    """Delete a season (Admin only)."""
    success = await service.delete_season(season_id)
    if not success:
        raise HTTPException(status_code=404, detail="Season not found")


# --- EPISODES ---

from app.domain.series.entities import EpisodeDetail

@router.get("/episodes/code/{code}", response_model=EpisodeDetail)
@limiter.limit("120/minute")
async def get_episode_by_code(
    request: Request,
    code: str,
    service: SeriesService = Depends(get_series_service)
):
    """Get episode details by code (Public, for Bot)."""
    episode = await service.get_episode_detail_by_code(code)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode

@router.post("/seasons/{season_id}/episodes", response_model=Episode, status_code=status.HTTP_201_CREATED)
async def create_episode(
    season_id: int,
    episode_in: EpisodeCreate,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_admin_or_bot)
):
    """Create a new episode for a season (Admin or Bot)."""
    if episode_in.season_id != season_id:
        raise HTTPException(status_code=400, detail="Season ID mismatch")
        
    try:
        return await service.create_episode(episode_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/seasons/{season_id}/episodes", response_model=List[Episode])
@limiter.limit("120/minute")
async def list_episodes(
    request: Request,
    season_id: int,
    service: SeriesService = Depends(get_series_service)
):
    """Get all episodes for a season (Public)."""
    season = await service.get_season_by_id(season_id)
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    return season.episodes


@router.put("/episodes/{episode_id}", response_model=Episode)
async def update_episode(
    episode_id: int,
    episode_in: EpisodeUpdate,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    """Update an episode (Admin only)."""
    episode = await service.update_episode(episode_id, episode_in)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode


@router.delete("/episodes/{episode_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_episode(
    episode_id: int,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    """Delete an episode (Admin only)."""
    success = await service.delete_episode(episode_id)
    if not success:
        raise HTTPException(status_code=404, detail="Episode not found")


class UploadJobResponse(BaseModel):
    job_id: str
    status: str
    message: str


@router.post("/episodes/{episode_id}/upload-video", response_model=UploadJobResponse)
async def upload_episode_video(
    episode_id: int,
    request: Request,
    file: UploadFile = File(...),
    language: str = Form("Asosiy"),
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    """Qism videosini qabul qilib, orqa fonda Telegram'ga yuklaydi."""
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Faqat video fayllar ruxsat etiladi.")

    suffix = os.path.splitext(file.filename or "video.mp4")[1] or ".mp4"
    tmp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    tmp_path = tmp_file.name

    try:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break
            tmp_file.write(chunk)
        tmp_file.close()
    except HTTPException:
        raise
    except Exception as e:
        try:
            tmp_file.close()
            os.remove(tmp_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail="Faylni saqlashda xato.")

    job_id = await job_manager.create_job(meta={"episode_id": episode_id, "language": language})

    async def _background_upload():
        await job_manager.set_processing(job_id, progress=5)
        try:
            async def _on_progress(pct: int):
                await job_manager.set_progress(job_id, pct)

            file_id, message_id = await telegram_client.send_video_to_storage(
                tmp_path=tmp_path,
                filename=file.filename or "video.mp4",
                mime_type=file.content_type or "video/mp4",
                on_progress=lambda p: asyncio.ensure_future(_on_progress(p)),
            )

            episode = await service.add_episode_translation(
                episode_id=episode_id,
                language=language,
                file_id=file_id,
                message_id=message_id
            )
            if not episode:
                await job_manager.set_failed(job_id, "Qism topilmadi.")
                return
            await job_manager.set_done(job_id, result={"episode_id": episode_id, "language": language})
        except Exception as e:
            err_msg = str(e)
            logger.error(f"Background upload failed for job {job_id}: {err_msg}", exc_info=True)
            await job_manager.set_failed(job_id, err_msg)
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    asyncio.create_task(_background_upload())
    await job_manager.cleanup_old_jobs()

    return UploadJobResponse(
        job_id=job_id,
        status=JobStatus.PROCESSING,
        message="Video qabul qilindi. Telegram'ga yuklanmoqda..."
    )


@router.get("/episodes/{episode_id}/upload-jobs/{job_id}")
async def get_episode_upload_job_status(
    episode_id: int,
    job_id: str,
    admin: dict = Depends(get_current_admin)
):
    """Episode background upload job statusini tekshirish."""
    job = await job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job topilmadi.")
    return job


class LinkVideoRequest(BaseModel):
    message_id: int
    language: str = "Asosiy"

@router.post("/episodes/{episode_id}/link-video", response_model=Episode)
async def link_episode_video(
    episode_id: int,
    request: LinkVideoRequest,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_admin_or_bot)
):
    try:
        episode = await service.link_episode_video_from_message(episode_id, request.message_id, request.language)
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")
        return episode
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in link_episode_video endpoint for episode {episode_id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Xabardan video olishda kutilmagan xatolik.")

@router.delete("/episodes/translations/{translation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_episode_translation(
    translation_id: int,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    """Delete an episode translation (Admin only)."""
    success = await service.delete_episode_translation(translation_id)
    if not success:
        raise HTTPException(status_code=404, detail="Translation not found")

