"""Real-time view tracking and analytics aggregation helpers."""
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Literal

from sqlalchemy import case, desc, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_cache, set_cache
from app.infrastructure.db.models.content_request import ContentRequestModel
from app.infrastructure.db.models.media_view_event import MediaViewEventModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import EpisodeModel, SeasonModel, SeriesModel
from app.infrastructure.db.models.series_subscription import SeriesSubscriptionModel
from app.infrastructure.db.models.user import UserModel

logger = logging.getLogger(__name__)

ViewSource = Literal["bot", "web", "stream"]


async def _resolve_series_id_from_episode(
    session: AsyncSession, episode_id: int
) -> int | None:
    stmt = (
        select(SeasonModel.series_id)
        .join(EpisodeModel, EpisodeModel.season_id == SeasonModel.id)
        .where(EpisodeModel.id == episode_id)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


async def record_media_view(
    session: AsyncSession,
    *,
    media_type: Literal["movie", "series"],
    movie_id: int | None = None,
    series_id: int | None = None,
    episode_id: int | None = None,
    source: ViewSource = "web",
    user_id: int | None = None,
    dedup_key: str | None = None,
    dedup_ttl_seconds: int = 3600,
) -> bool:
    """
    Record a single media view event and atomically increment view_count.
    Returns False if skipped by dedup cache or invalid target.
    """
    if dedup_key:
        try:
            if await get_cache(f"view_dedup:{dedup_key}"):
                return False
        except Exception as exc:
            logger.debug("View dedup cache read failed for %s: %s", dedup_key, exc)

    resolved_series_id = series_id
    if media_type == "series" and not resolved_series_id and episode_id:
        resolved_series_id = await _resolve_series_id_from_episode(session, episode_id)

    if media_type == "movie" and not movie_id:
        return False
    if media_type == "series" and not resolved_series_id:
        return False

    if media_type == "movie":
        res = await session.execute(
            update(MovieModel)
            .where(MovieModel.id == movie_id)
            .values(view_count=MovieModel.view_count + 1)
        )
        if not res.rowcount:
            return False
    else:
        res = await session.execute(
            update(SeriesModel)
            .where(SeriesModel.id == resolved_series_id)
            .values(view_count=SeriesModel.view_count + 1)
        )
        if not res.rowcount:
            return False

    event = MediaViewEventModel(
        media_type=media_type,
        movie_id=movie_id if media_type == "movie" else None,
        series_id=resolved_series_id if media_type == "series" else None,
        episode_id=episode_id,
        source=source,
        user_id=user_id,
    )
    session.add(event)
    await session.commit()

    if dedup_key:
        try:
            await set_cache(f"view_dedup:{dedup_key}", "1", ttl_seconds=dedup_ttl_seconds)
        except Exception as exc:
            logger.debug("View dedup cache write failed for %s: %s", dedup_key, exc)

    return True


async def _fetch_top_movies(
    session: AsyncSession, since_utc: datetime | None, limit: int = 10
) -> list[dict[str, Any]]:
    if since_utc is not None:
        stmt = (
            select(
                MovieModel.id,
                MovieModel.title,
                MovieModel.code,
                MovieModel.short_code,
                MovieModel.poster_url,
                MovieModel.imdb_rating,
                MovieModel.release_year,
                MovieModel.view_count,
                func.count(MediaViewEventModel.id).label("period_views"),
            )
            .join(MediaViewEventModel, MediaViewEventModel.movie_id == MovieModel.id)
            .where(MediaViewEventModel.created_at >= since_utc)
            .group_by(MovieModel.id)
            .order_by(desc("period_views"), desc(MovieModel.view_count), desc(MovieModel.id))
            .limit(limit)
        )
        rows = (await session.execute(stmt)).all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "code": r.code,
                "short_code": r.short_code,
                "poster_url": r.poster_url,
                "imdb_rating": r.imdb_rating,
                "release_year": r.release_year,
                "total_views": r.view_count or 0,
                "period_views": int(r.period_views or 0),
            }
            for r in rows
        ]

    stmt = (
        select(
            MovieModel.id,
            MovieModel.title,
            MovieModel.code,
            MovieModel.short_code,
            MovieModel.poster_url,
            MovieModel.imdb_rating,
            MovieModel.release_year,
            MovieModel.view_count,
        )
        .where(MovieModel.view_count > 0)
        .order_by(desc(MovieModel.view_count), desc(MovieModel.id))
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "code": r.code,
            "short_code": r.short_code,
            "poster_url": r.poster_url,
            "imdb_rating": r.imdb_rating,
            "release_year": r.release_year,
            "total_views": r.view_count or 0,
            "period_views": r.view_count or 0,
        }
        for r in rows
    ]


async def _fetch_top_series(
    session: AsyncSession, since_utc: datetime | None, limit: int = 10
) -> list[dict[str, Any]]:
    sub_counts_subq = (
        select(
            SeriesSubscriptionModel.series_id,
            func.count(SeriesSubscriptionModel.id).label("sub_count"),
        )
        .group_by(SeriesSubscriptionModel.series_id)
        .subquery()
    )

    if since_utc is not None:
        stmt = (
            select(
                SeriesModel.id,
                SeriesModel.title,
                SeriesModel.poster_url,
                SeriesModel.imdb_rating,
                SeriesModel.release_year,
                SeriesModel.status,
                SeriesModel.view_count,
                func.count(MediaViewEventModel.id).label("period_views"),
                func.coalesce(sub_counts_subq.c.sub_count, 0).label("subscribers_count"),
            )
            .join(MediaViewEventModel, MediaViewEventModel.series_id == SeriesModel.id)
            .outerjoin(sub_counts_subq, sub_counts_subq.c.series_id == SeriesModel.id)
            .where(MediaViewEventModel.created_at >= since_utc)
            .group_by(SeriesModel.id, sub_counts_subq.c.sub_count)
            .order_by(desc("period_views"), desc(SeriesModel.view_count), desc(SeriesModel.id))
            .limit(limit)
        )
        rows = (await session.execute(stmt)).all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "poster_url": r.poster_url,
                "imdb_rating": r.imdb_rating,
                "release_year": r.release_year,
                "status": r.status,
                "total_views": r.view_count or 0,
                "period_views": int(r.period_views or 0),
                "subscribers_count": int(r.subscribers_count or 0),
            }
            for r in rows
        ]

    stmt = (
        select(
            SeriesModel.id,
            SeriesModel.title,
            SeriesModel.poster_url,
            SeriesModel.imdb_rating,
            SeriesModel.release_year,
            SeriesModel.status,
            SeriesModel.view_count,
            func.coalesce(sub_counts_subq.c.sub_count, 0).label("subscribers_count"),
        )
        .outerjoin(sub_counts_subq, sub_counts_subq.c.series_id == SeriesModel.id)
        .where(SeriesModel.view_count > 0)
        .order_by(desc(SeriesModel.view_count), desc(SeriesModel.id))
        .limit(limit)
    )
    rows = (await session.execute(stmt)).all()
    return [
        {
            "id": r.id,
            "title": r.title,
            "poster_url": r.poster_url,
            "imdb_rating": r.imdb_rating,
            "release_year": r.release_year,
            "status": r.status,
            "total_views": r.view_count or 0,
            "period_views": r.view_count or 0,
            "subscribers_count": int(r.subscribers_count or 0),
        }
        for r in rows
    ]


async def _fetch_daily_trend(
    session: AsyncSession, trend_days: int
) -> list[dict[str, Any]]:
    now_utc = datetime.now(timezone.utc)
    start_day = (now_utc - timedelta(days=trend_days - 1)).date()
    start_dt = datetime(start_day.year, start_day.month, start_day.day, tzinfo=timezone.utc)

    day_expr = func.date(MediaViewEventModel.created_at)
    stmt = (
        select(
            day_expr.label("day"),
            func.sum(case((MediaViewEventModel.source == "bot", 1), else_=0)).label("bot"),
            func.sum(case((MediaViewEventModel.source == "web", 1), else_=0)).label("web"),
            func.sum(case((MediaViewEventModel.source == "stream", 1), else_=0)).label("stream"),
            func.count(MediaViewEventModel.id).label("total"),
        )
        .where(MediaViewEventModel.created_at >= start_dt)
        .group_by(day_expr)
        .order_by(day_expr)
    )
    rows = (await session.execute(stmt)).all()
    by_day = {
        str(r.day)[:10]: {
            "bot": int(r.bot or 0),
            "web": int(r.web or 0),
            "stream": int(r.stream or 0),
            "total": int(r.total or 0),
        }
        for r in rows
    }

    trend: list[dict[str, Any]] = []
    for offset in range(trend_days):
        d = (start_day + timedelta(days=offset)).isoformat()
        counts = by_day.get(d, {"bot": 0, "web": 0, "stream": 0, "total": 0})
        trend.append({"date": d, **counts})
    return trend


async def get_analytics_overview(
    session: AsyncSession, days: int = 7
) -> dict[str, Any]:
    """Compute real analytics metrics for Admin Analytics page."""
    now_utc = datetime.now(timezone.utc)
    now_naive = now_utc.replace(tzinfo=None)
    today_naive = now_naive.replace(hour=0, minute=0, second=0, microsecond=0)
    since_utc = (
        now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        if days == 1
        else (now_utc - timedelta(days=days) if days > 0 else None)
    )

    total_movie_views = (
        await session.execute(select(func.coalesce(func.sum(MovieModel.view_count), 0)))
    ).scalar() or 0
    total_series_views = (
        await session.execute(select(func.coalesce(func.sum(SeriesModel.view_count), 0)))
    ).scalar() or 0
    total_views = int(total_movie_views) + int(total_series_views)

    source_stmt = select(
        func.count(MediaViewEventModel.id).label("total"),
        func.sum(case((MediaViewEventModel.source == "bot", 1), else_=0)).label("bot"),
        func.sum(case((MediaViewEventModel.source == "web", 1), else_=0)).label("web"),
        func.sum(case((MediaViewEventModel.source == "stream", 1), else_=0)).label("stream"),
    )
    if since_utc is not None:
        source_stmt = source_stmt.where(MediaViewEventModel.created_at >= since_utc)
    src_row = (await session.execute(source_stmt)).first()

    total_users = (await session.execute(select(func.count(UserModel.id)))).scalar() or 0
    active_today = (
        await session.execute(
            select(func.count(UserModel.id)).where(UserModel.last_active_at >= today_naive)
        )
    ).scalar() or 0
    active_7d = (
        await session.execute(
            select(func.count(UserModel.id)).where(
                UserModel.last_active_at >= now_naive - timedelta(days=7)
            )
        )
    ).scalar() or 0
    active_30d = (
        await session.execute(
            select(func.count(UserModel.id)).where(
                UserModel.last_active_at >= now_naive - timedelta(days=30)
            )
        )
    ).scalar() or 0

    total_requests = (
        await session.execute(select(func.count(ContentRequestModel.id)))
    ).scalar() or 0
    pending_requests = (
        await session.execute(
            select(func.count(ContentRequestModel.id)).where(
                ContentRequestModel.status.in_(["pending", "in_review"])
            )
        )
    ).scalar() or 0

    top_req_rows = (
        await session.execute(
            select(ContentRequestModel)
            .where(ContentRequestModel.status.in_(["pending", "in_review"]))
            .order_by(desc(ContentRequestModel.vote_count), desc(ContentRequestModel.created_at))
            .limit(10)
        )
    ).scalars().all()

    top_movies = await _fetch_top_movies(session, since_utc, limit=10)
    top_series = await _fetch_top_series(session, since_utc, limit=10)
    trend_days = min(max(days if days > 0 else 14, 1), 30)
    daily_trend = await _fetch_daily_trend(session, trend_days)

    return {
        "days": days,
        "summary": {
            "total_views": total_views,
            "period_views": int((src_row.total if src_row else 0) or 0),
            "bot_views": int((src_row.bot if src_row else 0) or 0),
            "web_views": int((src_row.web if src_row else 0) or 0),
            "stream_views": int((src_row.stream if src_row else 0) or 0),
            "total_users": int(total_users),
            "active_users_today": int(active_today),
            "active_users_7d": int(active_7d),
            "active_users_30d": int(active_30d),
            "total_requests": int(total_requests),
            "pending_requests": int(pending_requests),
        },
        "top_movies": top_movies,
        "top_series": top_series,
        "top_requests": [
            {
                "id": r.id,
                "title": r.title,
                "original_title": r.original_title,
                "media_type": r.media_type,
                "release_year": r.release_year,
                "poster_url": r.poster_url,
                "tmdb_id": r.tmdb_id,
                "vote_count": r.vote_count,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in top_req_rows
        ],
        "daily_trend": daily_trend,
    }
