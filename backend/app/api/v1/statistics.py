"""API v1 — Statistics endpoints."""
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_current_admin
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel

router = APIRouter(prefix="/statistics", tags=["statistics"])


class RecentContentItem(BaseModel):
    id: int
    title: str
    type: str  # "kino" | "serial"
    status: str
    poster_url: Optional[str] = None
    created_at: datetime


class DashboardStatsResponse(BaseModel):
    total_users: int
    new_users_today: int
    total_movies: int
    total_series: int
    recent_items: List[RecentContentItem]


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_statistics(
    session: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
) -> DashboardStatsResponse:
    """Get aggregated statistics for admin dashboard."""
    # 1. Total counts
    total_users = (await session.execute(select(func.count(UserModel.id)))).scalar() or 0
    total_movies = (await session.execute(select(func.count(MovieModel.id)))).scalar() or 0
    total_series = (await session.execute(select(func.count(SeriesModel.id)))).scalar() or 0

    # 2. Today's new users
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None)
    new_users_today = (await session.execute(
        select(func.count(UserModel.id)).where(UserModel.joined_at >= today_start)
    )).scalar() or 0

    # 3. Recent movies (top 5 by created_at)
    recent_movies_rows = (await session.execute(
        select(
            MovieModel.id,
            MovieModel.title,
            MovieModel.poster_url,
            MovieModel.created_at
        ).order_by(desc(MovieModel.created_at)).limit(5)
    )).all()

    # 4. Recent series (top 5 by created_at)
    recent_series_rows = (await session.execute(
        select(
            SeriesModel.id,
            SeriesModel.title,
            SeriesModel.poster_url,
            SeriesModel.status,
            SeriesModel.created_at
        ).order_by(desc(SeriesModel.created_at)).limit(5)
    )).all()

    items: List[RecentContentItem] = []
    for m in recent_movies_rows:
        items.append(RecentContentItem(
            id=m.id,
            title=m.title,
            type="kino",
            status="Faol",
            poster_url=m.poster_url,
            created_at=m.created_at,
        ))

    for s in recent_series_rows:
        status_label = "Faol"
        if s.status:
            status_lower = s.status.lower()
            if status_lower in ["ongoing", "jarayonda"]:
                status_label = "Jarayonda"
            elif status_lower in ["completed", "yakunlangan", "tamomlangan"]:
                status_label = "Tugallangan"
            else:
                status_label = s.status
        items.append(RecentContentItem(
            id=s.id,
            title=s.title,
            type="serial",
            status=status_label,
            poster_url=s.poster_url,
            created_at=s.created_at,
        ))

    items.sort(key=lambda x: x.created_at, reverse=True)
    recent_items = items[:5]

    return DashboardStatsResponse(
        total_users=total_users,
        new_users_today=new_users_today,
        total_movies=total_movies,
        total_series=total_series,
        recent_items=recent_items,
    )
