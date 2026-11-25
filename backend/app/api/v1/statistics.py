"""API v1 — Statistics, view tracking, analytics & TMDb insights endpoints."""
from datetime import datetime, timezone
from typing import Any, List, Literal, Optional
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_current_admin
from app.api.limiter import limiter
from app.core.analytics import get_analytics_overview, record_media_view
from app.core.cache import get_cache, set_cache
from app.infrastructure.db.models.content_request import ContentRequestModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.external.tmdb_client import TMDB_IMAGE_BASE, TMDbClient

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


class TrackViewRequest(BaseModel):
    media_type: Literal["movie", "series"]
    movie_id: int | None = None
    series_id: int | None = None
    episode_id: int | None = None
    source: Literal["web", "bot", "stream"] = "web"


class TrackViewResponse(BaseModel):
    recorded: bool


@router.get("/dashboard", response_model=DashboardStatsResponse)
async def get_dashboard_statistics(
    session: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
) -> DashboardStatsResponse:
    """Get aggregated statistics for admin dashboard."""
    total_users = (await session.execute(select(func.count(UserModel.id)))).scalar() or 0
    total_movies = (await session.execute(select(func.count(MovieModel.id)))).scalar() or 0
    total_series = (await session.execute(select(func.count(SeriesModel.id)))).scalar() or 0

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).replace(tzinfo=None)
    new_users_today = (await session.execute(
        select(func.count(UserModel.id)).where(UserModel.joined_at >= today_start)
    )).scalar() or 0

    recent_movies_rows = (await session.execute(
        select(
            MovieModel.id,
            MovieModel.title,
            MovieModel.poster_url,
            MovieModel.created_at
        ).order_by(desc(MovieModel.created_at)).limit(5)
    )).all()

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


@router.post("/track-view", response_model=TrackViewResponse)
@limiter.limit("60/minute")
async def track_media_view(
    request: Request,
    payload: TrackViewRequest,
    session: AsyncSession = Depends(get_db_session),
) -> TrackViewResponse:
    """Record a view from website/stream with IP deduplication."""
    target_id = payload.movie_id or payload.series_id or payload.episode_id
    if not target_id:
        return TrackViewResponse(recorded=False)

    client_ip = request.client.host if request.client else "unknown"
    dedup_key = f"{payload.source}:{client_ip}:{payload.media_type}:{target_id}"
    recorded = await record_media_view(
        session,
        media_type=payload.media_type,
        movie_id=payload.movie_id,
        series_id=payload.series_id,
        episode_id=payload.episode_id,
        source=payload.source,
        dedup_key=dedup_key,
        dedup_ttl_seconds=3600,
    )
    return TrackViewResponse(recorded=recorded)


@router.get("/analytics")
async def get_admin_analytics(
    days: int = Query(7, ge=0, le=365, description="0=barchasi, 1=bugun, 7=hafta, 30=oy"),
    session: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
) -> dict[str, Any]:
    """Full analytics overview: top viewed movies/series, active users, requests, daily trend."""
    cache_key = f"cache:stats:analytics:{days}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    data = await get_analytics_overview(session, days=days)
    await set_cache(cache_key, data, ttl_seconds=120)
    return data


@router.get("/tmdb-insights")
async def get_tmdb_insights(
    category: Literal["trending_day", "trending_week", "upcoming", "now_playing", "tv_on_the_air"] = Query("trending_week"),
    page: int = Query(1, ge=1, le=5),
    session: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
) -> dict[str, Any]:
    """Fetch TMDb trending/upcoming/premieres and cross-reference against local library and requests."""
    cache_key = f"cache:stats:tmdb_insights:{category}:{page}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    client = TMDbClient()
    raw = await client.get_feed(category=category, page=page)
    results = raw.get("results") or []

    tmdb_ids = [int(r["id"]) for r in results if r.get("id")]
    movie_map: dict[int, tuple[int, str | None]] = {}
    series_map: dict[int, int] = {}
    request_map: dict[int, tuple[int, int, str]] = {}

    if tmdb_ids:
        m_rows = (
            await session.execute(
                select(MovieModel.tmdb_id, MovieModel.id, MovieModel.short_code, MovieModel.code)
                .where(MovieModel.tmdb_id.in_(tmdb_ids))
            )
        ).all()
        for r in m_rows:
            if r.tmdb_id is not None:
                movie_map[int(r.tmdb_id)] = (r.id, r.short_code or r.code)

        s_rows = (
            await session.execute(
                select(SeriesModel.tmdb_id, SeriesModel.id).where(SeriesModel.tmdb_id.in_(tmdb_ids))
            )
        ).all()
        for r in s_rows:
            if r.tmdb_id is not None:
                series_map[int(r.tmdb_id)] = r.id

        req_rows = (
            await session.execute(
                select(
                    ContentRequestModel.tmdb_id,
                    ContentRequestModel.id,
                    ContentRequestModel.vote_count,
                    ContentRequestModel.status,
                ).where(ContentRequestModel.tmdb_id.in_(tmdb_ids))
            )
        ).all()
        for r in req_rows:
            if r.tmdb_id is not None:
                request_map[int(r.tmdb_id)] = (r.id, int(r.vote_count or 0), r.status)

    items: list[dict[str, Any]] = []
    for item in results:
        tid = item.get("id")
        if not tid:
            continue
        tid_int = int(tid)
        raw_media_type = item.get("media_type")
        if raw_media_type not in ("movie", "tv"):
            raw_media_type = "tv" if category == "tv_on_the_air" else "movie"
        norm_type = "series" if raw_media_type == "tv" else "movie"

        title = item.get("title") or item.get("name") or item.get("original_title") or item.get("original_name") or "Noma'lum"
        orig_title = item.get("original_title") or item.get("original_name")
        release_date = item.get("release_date") or item.get("first_air_date")
        release_year = int(release_date[:4]) if release_date and len(release_date) >= 4 and release_date[:4].isdigit() else None
        poster_path = item.get("poster_path")
        poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None

        in_library = False
        library_id: int | None = None
        library_code: str | None = None
        if norm_type == "movie" and tid_int in movie_map:
            in_library = True
            library_id, library_code = movie_map[tid_int]
        elif norm_type == "series" and tid_int in series_map:
            in_library = True
            library_id = series_map[tid_int]
            library_code = f"s_{library_id}"

        req_info = request_map.get(tid_int)
        items.append({
            "tmdb_id": tid_int,
            "media_type": norm_type,
            "title": title,
            "original_title": orig_title,
            "release_date": release_date,
            "release_year": release_year,
            "poster_url": poster_url,
            "overview": item.get("overview") or "",
            "vote_average": round(float(item.get("vote_average") or 0.0), 1),
            "vote_count": int(item.get("vote_count") or 0),
            "popularity": round(float(item.get("popularity") or 0.0), 1),
            "in_library": in_library,
            "library_id": library_id,
            "library_code": library_code,
            "is_requested": req_info is not None,
            "request_id": req_info[0] if req_info else None,
            "request_votes": req_info[1] if req_info else 0,
            "request_status": req_info[2] if req_info else None,
        })

    payload = {
        "category": category,
        "page": raw.get("page", page),
        "total_pages": min(int(raw.get("total_pages") or 1), 5),
        "total_results": int(raw.get("total_results") or len(items)),
        "items": items,
    }
    await set_cache(cache_key, payload, ttl_seconds=600)
    return payload
