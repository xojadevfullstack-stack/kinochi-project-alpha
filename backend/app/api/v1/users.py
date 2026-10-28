"""API v1 — Users endpoints."""
import logging
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
from app.infrastructure.db.models.series_subscription import SeriesSubscriptionModel
from app.infrastructure.db.models.collection_subscription import CollectionSubscriptionModel
from app.infrastructure.db.models.collection import CollectionModel
from app.core.recommendations import get_user_recommendations
from app.core.achievements import ACHIEVEMENTS
from sqlalchemy.orm import selectinload
from sqlalchemy import select, desc, func
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

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

@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    user_data: dict = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """Get profile of the currently logged in user."""
    user = await service.get_by_telegram_id(user_data["telegram_id"])
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")
    return user

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
                "code": record.movie.code,
                "release_year": record.movie.release_year,
                "imdb_rating": record.movie.imdb_rating,
                "genres": record.movie.genres
            }
        elif record.episode:
            item_data["type"] = "episode"
            s_obj = record.episode.season.series if (record.episode.season and record.episode.season.series) else None
            item_data["episode"] = {
                "id": record.episode.id,
                "display_code": record.episode.display_code,
                "code": record.episode.code,
                "season_number": record.episode.season.season_number if record.episode.season else 1,
                "episode_number": record.episode.episode_number,
                "series_id": s_obj.id if s_obj else None,
                "series_title": s_obj.title if s_obj else "Serial",
                "series_poster": s_obj.poster_url if s_obj else None,
                "release_year": s_obj.release_year if s_obj else None,
                "imdb_rating": s_obj.imdb_rating if s_obj else None,
                "genres": (s_obj.categories[0].name if (s_obj and s_obj.categories) else "Serial") if s_obj else "Serial"
            }
        items.append(item_data)
        
    return {"items": items, "total": len(items)}
    # Accurate total requires a separate count query, simplified for now.

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

@router.get("/me/subscriptions")
async def get_my_subscriptions(
    user: dict = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session)
):
    """Get active series and collection subscriptions for the currently authenticated user."""
    tg_id = user.get("telegram_id")
    if not tg_id:
        return {"series": [], "collections": [], "total": 0}

    # 1. Series Subscriptions
    stmt_sub = (
        select(SeriesSubscriptionModel)
        .where(SeriesSubscriptionModel.telegram_user_id == tg_id)
        .options(selectinload(SeriesSubscriptionModel.series))
        .order_by(desc(SeriesSubscriptionModel.created_at))
    )
    sub_records = (await session.execute(stmt_sub)).scalars().all()
    series_list = []
    for s in sub_records:
        if s.series:
            series_list.append({
                "id": s.series.id,
                "title": s.series.title,
                "poster_url": s.series.poster_url,
                "imdb_rating": s.series.imdb_rating,
                "release_year": s.series.release_year,
                "type": "series",
                "created_at": s.created_at.isoformat() if s.created_at else None
            })

    # 2. Collection / Franchise Subscriptions
    stmt_col_sub = (
        select(CollectionSubscriptionModel)
        .where(CollectionSubscriptionModel.telegram_user_id == tg_id)
        .options(
            selectinload(CollectionSubscriptionModel.collection)
            .selectinload(CollectionModel.items)
        )
        .order_by(desc(CollectionSubscriptionModel.created_at))
    )
    col_sub_records = (await session.execute(stmt_col_sub)).scalars().all()
    collections_list = []
    for cs in col_sub_records:
        if cs.collection:
            collections_list.append({
                "id": cs.collection.id,
                "name": cs.collection.name,
                "slug": cs.collection.slug,
                "description": cs.collection.description,
                "poster_url": cs.collection.poster_url,
                "banner_url": cs.collection.banner_url,
                "is_franchise": cs.collection.is_franchise,
                "category_type": getattr(cs.collection, "category_type", "franchise"),
                "item_count": len(cs.collection.items) if cs.collection.items else 0,
                "type": "franchise" if cs.collection.is_franchise else "collection",
                "created_at": cs.created_at.isoformat() if cs.created_at else None
            })

    return {
        "series": series_list,
        "collections": collections_list,
        "total": len(series_list) + len(collections_list)
    }


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


@router.get("/by-telegram/{telegram_id}/summary", dependencies=[Depends(verify_bot_secret)])
async def get_user_summary_by_telegram(
    telegram_id: int,
    session: AsyncSession = Depends(get_db_session),
    service: UserService = Depends(get_user_service),
):
    """Full user profile summary for Telegram Bot (Profile, Watch History, Achievements, Subscriptions, Recommendations)."""
    user = await service.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi")

    # 1. Watch history (latest 5)
    stmt_wh = (
        select(WatchHistoryModel)
        .where(WatchHistoryModel.user_id == user.id)
        .order_by(desc(WatchHistoryModel.last_watched_at))
        .limit(5)
        .options(
            selectinload(WatchHistoryModel.movie),
            selectinload(WatchHistoryModel.episode).selectinload(EpisodeModel.season).selectinload(SeasonModel.series)
        )
    )
    history_records = (await session.execute(stmt_wh)).scalars().all()
    history_items = []
    for h in history_records:
        if h.movie:
            history_items.append({
                "type": "movie",
                "title": h.movie.title,
                "code": h.movie.code,
                "status": h.status
            })
        elif h.episode and h.episode.season and h.episode.season.series:
            history_items.append({
                "type": "episode",
                "title": f"{h.episode.season.series.title} ({h.episode.season.season_number}-mavsum, {h.episode.episode_number}-qism)",
                "code": h.episode.display_code or h.episode.code,
                "status": h.status
            })

    total_history = (await session.execute(
        select(func.count(WatchHistoryModel.id)).where(WatchHistoryModel.user_id == user.id)
    )).scalar() or 0

    # 2. Achievements
    stmt_ach = (
        select(UserAchievementModel)
        .where(UserAchievementModel.user_id == user.id)
        .order_by(desc(UserAchievementModel.earned_at))
    )
    ach_records = (await session.execute(stmt_ach)).scalars().all()
    achievements = []
    for a in ach_records:
        achievements.append({
            "code": a.achievement_code,
            "title": ACHIEVEMENTS.get(a.achievement_code, a.achievement_code),
            "earned_at": a.earned_at.isoformat() if a.earned_at else None
        })

    # 3. Series Subscriptions
    stmt_sub = (
        select(SeriesSubscriptionModel)
        .where(SeriesSubscriptionModel.telegram_user_id == telegram_id)
        .options(selectinload(SeriesSubscriptionModel.series))
        .order_by(desc(SeriesSubscriptionModel.created_at))
    )
    sub_records = (await session.execute(stmt_sub)).scalars().all()
    subscriptions = []
    for s in sub_records:
        if s.series:
            subscriptions.append({
                "series_id": s.series.id,
                "title": s.series.title,
                "poster_url": s.series.poster_url,
                "rating": s.series.imdb_rating
            })

    # 4. Collection / Franchise Subscriptions
    stmt_col_sub = (
        select(CollectionSubscriptionModel)
        .where(CollectionSubscriptionModel.telegram_user_id == telegram_id)
        .options(selectinload(CollectionSubscriptionModel.collection))
        .order_by(desc(CollectionSubscriptionModel.created_at))
    )
    col_sub_records = (await session.execute(stmt_col_sub)).scalars().all()
    collection_subscriptions = []
    for cs in col_sub_records:
        if cs.collection:
            collection_subscriptions.append({
                "collection_id": cs.collection.id,
                "name": cs.collection.name,
                "slug": cs.collection.slug,
                "poster_url": cs.collection.poster_url,
                "banner_url": cs.collection.banner_url,
                "is_franchise": cs.collection.is_franchise,
                "category_type": getattr(cs.collection, "category_type", "franchise"),
            })

    # 5. Recommendations
    try:
        recs = await get_user_recommendations(user.id)
    except Exception as e:
        logger.warning(f"Error fetching recommendations: {e}")
        recs = []

    return {
        "user": {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "joined_at": user.joined_at.isoformat() if user.joined_at else None,
        },
        "total_watched": total_history,
        "recent_history": history_items,
        "achievements": achievements,
        "subscriptions": subscriptions,
        "collection_subscriptions": collection_subscriptions,
        "recommendations": recs[:5]
    }


