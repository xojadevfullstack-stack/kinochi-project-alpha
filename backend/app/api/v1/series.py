"""API v1 — Series endpoints."""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Form

from app.api.deps import get_series_service, get_current_admin
from app.application.series.series_service import SeriesService
from app.domain.series.entities import (
    Series, SeriesCreate, SeriesUpdate, PaginatedSeriesResponse,
    Season, SeasonCreate, SeasonUpdate,
    Episode, EpisodeCreate, EpisodeUpdate
)
from app.utils.telegram_link_parser import parse_telegram_link

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/series", tags=["series"])


# --- SERIES ---

@router.post("", response_model=Series, status_code=status.HTTP_201_CREATED)
async def create_series(
    series_in: SeriesCreate,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    """Create a new series (Admin only)."""
    if series_in.source_link:
        try:
            parsed = parse_telegram_link(series_in.source_link)
            series_in.source_chat_id = parsed["chat_id"]
            series_in.source_topic_id = parsed["topic_id"]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    return await service.create_series(series_in)


@router.get("", response_model=PaginatedSeriesResponse)
async def list_series(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: SeriesService = Depends(get_series_service)
):
    """List series (Public)."""
    items, total = await service.get_all_series(skip=skip, limit=limit)
    
    # Calculate pages
    pages = (total + limit - 1) // limit if total > 0 else 0
    page = (skip // limit) + 1 if limit > 0 else 1
    
    return PaginatedSeriesResponse(items=items, total=total, page=page, size=limit, pages=pages)


@router.get("/search", response_model=PaginatedSeriesResponse)
async def search_series(
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
async def get_series_by_source(
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
async def get_series(
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
    if series_in.source_link:
        try:
            parsed = parse_telegram_link(series_in.source_link)
            series_in.source_chat_id = parsed["chat_id"]
            series_in.source_topic_id = parsed["topic_id"]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    elif "source_link" in series_in.model_fields_set and series_in.source_link is None:
        series_in.source_chat_id = None
        series_in.source_topic_id = None
        
    series = await service.update_series(series_id, series_in)
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
async def list_seasons(
    series_id: int,
    service: SeriesService = Depends(get_series_service)
):
    """Get all seasons for a series (Public)."""
    series = await service.get_series_by_id(series_id)
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    return series.seasons

@router.get("/seasons/{season_id}", response_model=Season)
async def get_season(
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
async def get_episode_by_code(
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
    admin: dict = Depends(get_current_admin)
):
    """Create a new episode for a season (Admin only)."""
    if episode_in.season_id != season_id:
        raise HTTPException(status_code=400, detail="Season ID mismatch")
        
    try:
        return await service.create_episode(episode_in)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/seasons/{season_id}/episodes", response_model=List[Episode])
async def list_episodes(
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


@router.post("/episodes/{episode_id}/upload-video", response_model=Episode)
async def upload_episode_video(
    episode_id: int,
    file: UploadFile = File(...),
    language: str = Form("Asosiy"),
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    """Upload video for an episode to Telegram storage (Admin only)."""
    if not file.content_type or not file.content_type.startswith("video/"):
        raise HTTPException(status_code=400, detail="Faqat video fayllar ruxsat etiladi (MIME turi video/* bo'lishi kerak).")

    try:
        episode = await service.upload_episode_video(episode_id, file, language)
        if not episode:
            raise HTTPException(status_code=404, detail="Episode not found")
        return episode
    except Exception as e:
        logger.error(f"Error in upload_episode_video endpoint for episode {episode_id}: {str(e)}", exc_info=True)
        # Ensure we return a user-friendly error if it's too large or something else fails
        if "too large" in str(e).lower() or "memory" in str(e).lower():
            raise HTTPException(status_code=400, detail="Video hajmi juda katta.")
        raise HTTPException(status_code=500, detail="Video yuklashda xatolik yuz berdi.")

from pydantic import BaseModel
class LinkVideoRequest(BaseModel):
    message_id: int
    language: str = "Asosiy"

@router.post("/episodes/{episode_id}/link-video", response_model=Episode)
async def link_episode_video(
    episode_id: int,
    request: LinkVideoRequest,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
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

