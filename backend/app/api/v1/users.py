"""API v1 — Users endpoints."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header, Query, status
from pydantic import BaseModel

from app.api.deps import get_user_service, get_current_admin, get_current_user, get_db_session
from app.application.users.service import UserService
from app.core.config import settings
from app.infrastructure.db.models.watch_history import WatchHistoryModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import EpisodeModel, SeasonModel, SeriesModel
from app.infrastructure.db.models.achievement import UserAchievementModel
from app.core.recommendations import get_user_recommendations
from app.core.achievements import ACHIEVEMENTS
from sqlalchemy.orm import selectinload
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/users", tags=["users"])


# ── Bot internal API secret verification ─────────────────────────────────
async def verify_bot_secret(x_bot_secret: str = Header(..., alias="X-Bot-Secret")) -> None:
    """Dependency: verify that the request comes from our bot (not a random caller).
    The secret must match BOT_API_SECRET in .env.
    """
    if not settings.BOT_API_SECRET:
        raise HTTPException(
            status_code=500,
            detail="BOT_API_SECRET konfiguratsiyalanmagan. .env faylini tekshiring."
        )
    if x_bot_secret != settings.BOT_API_SECRET:
        raise HTTPException(
            status_code=403,
            detail="Forbidden: noto'g'ri bot secret."
        )


class UserCreateOrUpdate(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None

class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_admin: bool
    is_banned: bool
    joined_at: datetime
    last_active_at: datetime

    model_config = {"from_attributes": True}

class PaginatedUsersResponse(BaseModel):
    items: list[UserResponse]
    total: int

@router.post("/register", response_model=UserResponse,
             dependencies=[Depends(verify_bot_secret)])
async def register_or_update(
    user_in: UserCreateOrUpdate,
    service: UserService = Depends(get_user_service)
):
    """Register or update a user (Bot internal only — requires X-Bot-Secret header)."""
    return await service.register_or_update(**user_in.model_dump())

@router.get("/me/history")
async def get_my_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Read-only watch history for the frontend."""
    user_id = user["user_id"]
    
    # Query history
    stmt = (
        select(WatchHistoryModel)
        .where(WatchHistoryModel.user_id == user_id)
        .order_by(desc(WatchHistoryModel.last_watched_at))
        .offset(skip)
        .limit(limit)
        .options(
            selectinload(WatchHistoryModel.movie),
            selectinload(WatchHistoryModel.episode).selectinload(EpisodeModel.season).selectinload(SeasonModel.series)
        )
    )
    result = await session.execute(stmt)
    history_records = result.scalars().all()
    
    # Format response
    items = []
    for record in history_records:
        item_data = {
            "id": record.id,
            "status": record.status,
            "last_watched_at": record.last_watched_at,
        }
        if record.movie:
            item_data["type"] = "movie"
            item_data["movie"] = {
                "id": record.movie.id,
                "title": record.movie.title,
                "poster_url": record.movie.poster_url,
                "code": record.movie.code
            }
        elif record.episode:
            item_data["type"] = "episode"
            item_data["episode"] = {
                "id": record.episode.id,
                "display_code": record.episode.display_code,
                "code": record.episode.code,
                "season_number": record.episode.season.season_number,
                "episode_number": record.episode.episode_number,
                "series_id": record.episode.season.series.id,
                "series_title": record.episode.season.series.title,
                "series_poster": record.episode.season.series.poster_url
            }
        items.append(item_data)
        
    return {"items": items, "total": len(items)} # Accurate total requires a separate count query, simplified for now.

@router.get("/me/recommendations")
async def get_my_recommendations(user: dict = Depends(get_current_user)):
    """Get personalized recommendations based on watch history."""
    items = await get_user_recommendations(user["user_id"])
    return {"items": items}

@router.get("/me/achievements")
async def get_my_achievements(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Read-only achievements for the frontend."""
    user_id = user["user_id"]
    
    stmt = (
        select(UserAchievementModel)
        .where(UserAchievementModel.user_id == user_id)
        .order_by(desc(UserAchievementModel.earned_at))
    )
    result = await session.execute(stmt)
    records = result.scalars().all()
    
    items = []
    for record in records:
        items.append({
            "code": record.achievement_code,
            "title": ACHIEVEMENTS.get(record.achievement_code, record.achievement_code),
            "earned_at": record.earned_at
        })
        
    return {"items": items, "total": len(items)}

@router.get("", response_model=PaginatedUsersResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: UserService = Depends(get_user_service),
    admin: dict = Depends(get_current_admin)
):
    """List all users (Admin only)."""
    users, total = await service.list_users(skip=skip, limit=limit)
    return {"items": users, "total": total}

@router.get("/{telegram_id}", response_model=UserResponse)
async def get_user(
    telegram_id: int,
    service: UserService = Depends(get_user_service),
    admin: dict = Depends(get_current_admin)
):
    """Get user by telegram ID (Admin only)."""
    user = await service.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/{telegram_id}/ban", status_code=status.HTTP_204_NO_CONTENT)
async def ban_user(
    telegram_id: int,
    service: UserService = Depends(get_user_service),
    admin: dict = Depends(get_current_admin)
):
    """Ban a user (Admin only)."""
    success = await service.ban(telegram_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

@router.post("/{telegram_id}/unban", status_code=status.HTTP_204_NO_CONTENT)
async def unban_user(
    telegram_id: int,
    service: UserService = Depends(get_user_service),
    admin: dict = Depends(get_current_admin)
):
    """Unban a user (Admin only)."""
    success = await service.unban(telegram_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

