"""
FastAPI router for Series (Seasons and Episodes) management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.api.deps import get_db_session, get_current_admin
from app.api.schemas.series import (
    SeasonCreate, SeasonUpdate, SeasonResponse,
    EpisodeCreate, EpisodeUpdate, EpisodeResponse
)

from app.infrastructure.db.repositories.series_repo import SeriesRepositoryImpl
from app.infrastructure.db.repositories.movie_repo import MovieRepositoryImpl
from app.application.movies.series_service import SeriesService

router = APIRouter(prefix="/series", tags=["series"])

def get_series_service(session: AsyncSession = Depends(get_db_session)) -> SeriesService:
    series_repo = SeriesRepositoryImpl(session)
    movie_repo = MovieRepositoryImpl(session)
    return SeriesService(series_repo, movie_repo)

# ── Seasons ──────────────────────────────────────────────────────
@router.post("/movies/{movie_id}/seasons", response_model=SeasonResponse, status_code=status.HTTP_201_CREATED)
async def create_season(
    movie_id: int,
    data: SeasonCreate,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    try:
        return await service.create_season(movie_id, data.season_number, data.description)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/movies/{movie_id}/seasons", response_model=List[SeasonResponse])
async def list_seasons(
    movie_id: int,
    service: SeriesService = Depends(get_series_service)
):
    return await service.list_seasons(movie_id)

@router.put("/seasons/{season_id}", response_model=SeasonResponse)
async def update_season(
    season_id: int,
    data: SeasonUpdate,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    try:
        return await service.update_season(season_id, **data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/seasons/{season_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_season(
    season_id: int,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    success = await service.delete_season(season_id)
    if not success:
        raise HTTPException(status_code=404, detail="Season not found")

# ── Episodes ─────────────────────────────────────────────────────
@router.post("/seasons/{season_id}/episodes", response_model=EpisodeResponse, status_code=status.HTTP_201_CREATED)
async def create_episode(
    season_id: int,
    data: EpisodeCreate,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    try:
        return await service.create_episode(
            season_id=season_id,
            episode_number=data.episode_number,
            title=data.title,
            telegram_file_id=data.telegram_file_id,
            storage_channel_message_id=data.storage_channel_message_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/seasons/{season_id}/episodes", response_model=List[EpisodeResponse])
async def list_episodes(
    season_id: int,
    service: SeriesService = Depends(get_series_service)
):
    return await service.list_episodes(season_id)

@router.get("/episodes/code/{code}", response_model=EpisodeResponse)
async def get_episode_by_code(
    code: str,
    service: SeriesService = Depends(get_series_service)
):
    episode = await service.get_episode_by_code(code)
    if not episode:
        raise HTTPException(status_code=404, detail="Episode not found")
    return episode

@router.put("/episodes/{episode_id}", response_model=EpisodeResponse)
async def update_episode(
    episode_id: int,
    data: EpisodeUpdate,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    try:
        return await service.update_episode(episode_id, **data.model_dump(exclude_unset=True))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/episodes/{episode_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_episode(
    episode_id: int,
    service: SeriesService = Depends(get_series_service),
    admin: dict = Depends(get_current_admin)
):
    success = await service.delete_episode(episode_id)
    if not success:
        raise HTTPException(status_code=404, detail="Episode not found")
