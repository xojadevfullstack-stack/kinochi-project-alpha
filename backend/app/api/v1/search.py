"""
API v1 — Search endpoints.
Provides ultra-fast debounced live search for website autocomplete and Telegram bot.
"""
import logging
import re
from typing import Literal
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, or_, func, case, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.api.limiter import limiter
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import EpisodeModel, SeasonModel, SeriesModel
from app.infrastructure.db.models.collection import CollectionModel
from app.infrastructure.db.query_filters import exclude_adult_media, non_adult_condition, published_only
from app.core.cache import delete_cache_pattern, get_cache, set_cache

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


class LiveSearchResultItem(BaseModel):
    id: int
    title: str
    original_title: str | None = None
    code: str
    short_code: str | None = None
    year: int | None = None
    poster_url: str | None = None
    imdb_rating: float | None = None
    type: Literal["movie", "series", "collection"]
    extra: str | None = None
    search_count: int = 0
    view_count: int = 0


class LiveSearchResponse(BaseModel):
    query: str
    total: int
    results: list[LiveSearchResultItem]


class SearchClickTrackRequest(BaseModel):
    media_type: Literal["movie", "series"]
    item_id: int


class SearchClickTrackResponse(BaseModel):
    recorded: bool


@router.get("/popular", response_model=LiveSearchResponse)
@limiter.limit("120/minute")
async def popular_searches(
    request: Request,
    limit: int = Query(8, ge=1, le=20, description="Eng ko'p qidirilganlar soni"),
    include_adult: bool = Query(False, description="Include 18+ content"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Return most-searched movies and series (falling back to view_count and IMDb rating).
    Shown immediately when the user clicks the search bar before typing.
    """
    cache_key = f"cache:search:popular:{include_adult}:{limit}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    movie_stmt = select(MovieModel).order_by(
        desc(MovieModel.search_count),
        desc(MovieModel.view_count),
        MovieModel.imdb_rating.desc().nullslast(),
        desc(MovieModel.id),
    ).limit(limit)
    movie_stmt = published_only(movie_stmt, MovieModel)
    if not include_adult:
        movie_stmt = exclude_adult_media(movie_stmt, MovieModel)

    series_stmt = select(SeriesModel).order_by(
        desc(SeriesModel.search_count),
        desc(SeriesModel.view_count),
        SeriesModel.imdb_rating.desc().nullslast(),
        desc(SeriesModel.id),
    ).limit(limit)
    series_stmt = published_only(series_stmt, SeriesModel)
    if not include_adult:
        series_stmt = exclude_adult_media(series_stmt, SeriesModel)

    movie_rows = (await db.execute(movie_stmt)).scalars().all()
    series_rows = (await db.execute(series_stmt)).scalars().all()

    combined: list[LiveSearchResultItem] = []
    for m in movie_rows:
        combined.append(
            LiveSearchResultItem(
                id=m.id,
                title=m.title,
                original_title=m.original_title,
                code=m.code,
                short_code=m.short_code,
                year=m.release_year,
                poster_url=m.poster_url,
                imdb_rating=m.imdb_rating,
                type="movie",
                search_count=int(getattr(m, "search_count", 0) or 0),
                view_count=int(getattr(m, "view_count", 0) or 0),
            )
        )
    for s in series_rows:
        combined.append(
            LiveSearchResultItem(
                id=s.id,
                title=s.title,
                original_title=None,
                code=f"s_{s.id}",
                year=s.release_year,
                poster_url=s.poster_url,
                imdb_rating=s.imdb_rating,
                type="series",
                search_count=int(getattr(s, "search_count", 0) or 0),
                view_count=int(getattr(s, "view_count", 0) or 0),
            )
        )

    combined.sort(
        key=lambda x: (x.search_count, x.view_count, float(x.imdb_rating or 0.0), x.id),
        reverse=True,
    )
    trimmed = combined[:limit]
    resp = LiveSearchResponse(query="", total=len(trimmed), results=trimmed)
    await set_cache(cache_key, resp.model_dump(mode="json"), 120)
    return resp


@router.post("/track-click", response_model=SearchClickTrackResponse)
@limiter.limit("60/minute")
async def track_search_click(
    request: Request,
    payload: SearchClickTrackRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """Increment search_count when a user selects a searched movie/series (1h IP dedup)."""
    if payload.item_id <= 0:
        return SearchClickTrackResponse(recorded=False)

    client_ip = request.client.host if request.client else "unknown"
    dedup_key = f"search_click_dedup:{client_ip}:{payload.media_type}:{payload.item_id}"
    try:
        if await get_cache(dedup_key):
            return SearchClickTrackResponse(recorded=False)
    except Exception as exc:
        logger.debug("Search dedup cache read failed: %s", exc)

    if payload.media_type == "movie":
        res = await db.execute(
            update(MovieModel)
            .where(MovieModel.id == payload.item_id)
            .values(search_count=MovieModel.search_count + 1)
        )
    else:
        res = await db.execute(
            update(SeriesModel)
            .where(SeriesModel.id == payload.item_id)
            .values(search_count=SeriesModel.search_count + 1)
        )

    if not res.rowcount:
        return SearchClickTrackResponse(recorded=False)

    await db.commit()
    try:
        await set_cache(dedup_key, "1", ttl_seconds=3600)
        await delete_cache_pattern("cache:search:popular:*")
    except Exception as exc:
        logger.debug("Search dedup cache update failed: %s", exc)
    return SearchClickTrackResponse(recorded=True)


@router.get("/live", response_model=LiveSearchResponse)
@limiter.limit("180/minute")
async def live_search(
    request: Request,
    q: str = Query(..., min_length=1, description="Qidiruv matni yoki kod"),
    limit: int = Query(8, ge=1, le=20, description="Natijalar soni"),
    include_adult: bool = Query(True, description="Include 18+ content"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Live autocomplete search endpoint.
    Searches across movies, series, and franchises with instant response time.
    """
    clean_query = q.strip()
    if not clean_query:
        return LiveSearchResponse(query=q, total=0, results=[])

    cache_key = f"cache:search:live:{clean_query.lower()}:{limit}:{include_adult}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    results: list[LiveSearchResultItem] = []

    # Punctuation and space tolerance (e.g. 'aka uka' matches 'Aka-uka', 'spider man' matches 'Spider-Man')
    words = [w for w in re.split(r"[\s\-_:]+", clean_query) if w]
    word_wildcard = f"%{'%'.join(words)}%" if words else f"%{clean_query}%"

    # 1. Check if user typed a movie code or ID (e.g., "#BYVC33", "BYVC33", "#190", "190", "s_993")
    code_query = clean_query.lstrip("#").strip()
    series_id_target: int | None = None
    if code_query.lower().startswith("s_") and code_query[2:].isdigit():
        series_id_target = int(code_query[2:])
    elif code_query.isdigit():
        series_id_target = int(code_query)

    is_potential_code = (
        " " not in code_query
        and len(code_query) <= 8
        and (code_query.isdigit() or code_query.isupper() or code_query.lower().startswith("s_"))
    )

    if is_potential_code:
        # 1a. Check exact movie code or short_code first
        movie_code_stmt = published_only(
            select(MovieModel).where(
                or_(MovieModel.code.ilike(code_query), MovieModel.short_code == code_query)
            ).limit(1),
            MovieModel,
        )
        if not include_adult:
            movie_code_stmt = exclude_adult_media(movie_code_stmt, MovieModel)
        movie_by_code = (await db.execute(movie_code_stmt)).scalar_one_or_none()

        # 1b. Check exact episode short_code or code BEFORE any numeric ID fallback
        ep_match = None
        if not movie_by_code:
            ep_stmt = (
                select(EpisodeModel, SeasonModel, SeriesModel)
                .join(SeasonModel, EpisodeModel.season_id == SeasonModel.id)
                .join(SeriesModel, SeasonModel.series_id == SeriesModel.id)
                .where(
                    SeriesModel.publish_status == "published",
                    or_(
                        EpisodeModel.short_code == code_query,
                        func.lower(EpisodeModel.code) == func.lower(code_query),
                    ),
                )
                .limit(1)
            )
            if not include_adult:
                ep_stmt = ep_stmt.where(non_adult_condition(SeriesModel))
            ep_match = (await db.execute(ep_stmt)).first()

        if ep_match:
            ep_row, ep_season, ep_series = ep_match
            results.append(
                LiveSearchResultItem(
                    id=ep_series.id,
                    title=f"{ep_series.title} ({ep_season.season_number}-mavsum, {ep_row.episode_number}-qism)",
                    original_title=None,
                    code=ep_row.code,
                    short_code=ep_row.short_code,
                    year=ep_series.release_year,
                    poster_url=ep_series.poster_url,
                    imdb_rating=ep_series.imdb_rating,
                    type="series",
                    extra="Qism kodi bo'yicha topildi",
                )
            )

        if not movie_by_code and not ep_match and code_query.isdigit() and len(code_query) <= 9:
            num_id = int(code_query)
            if 0 < num_id <= 2_147_483_647:
                num_stmt = published_only(select(MovieModel).where(MovieModel.id == num_id).limit(1), MovieModel)
                if not include_adult:
                    num_stmt = exclude_adult_media(num_stmt, MovieModel)
                movie_by_code = (await db.execute(num_stmt)).scalar_one_or_none()
        if movie_by_code:
            results.append(
                LiveSearchResultItem(
                    id=movie_by_code.id,
                    title=movie_by_code.title,
                    original_title=movie_by_code.original_title,
                    code=movie_by_code.code,
                    short_code=movie_by_code.short_code,
                    year=movie_by_code.release_year,
                    poster_url=movie_by_code.poster_url,
                    imdb_rating=movie_by_code.imdb_rating,
                    type="movie",
                    extra="Kod bo'yicha topildi",
                )
            )

        if series_id_target and (code_query.lower().startswith("s_") or (not movie_by_code and not ep_match)):
            series_by_id_stmt = published_only(
                select(SeriesModel).where(SeriesModel.id == series_id_target).limit(1), SeriesModel
            )
            if not include_adult:
                series_by_id_stmt = exclude_adult_media(series_by_id_stmt, SeriesModel)
            series_by_id_res = await db.execute(series_by_id_stmt)
            series_by_id = series_by_id_res.scalar_one_or_none()
            if series_by_id and not any(r.id == series_by_id.id and r.type == "series" for r in results):
                results.append(
                    LiveSearchResultItem(
                        id=series_by_id.id,
                        title=series_by_id.title,
                        original_title=None,
                        code=f"s_{series_by_id.id}",
                        year=series_by_id.release_year,
                        poster_url=series_by_id.poster_url,
                        imdb_rating=series_by_id.imdb_rating,
                        type="series",
                        extra="ID bo'yicha topildi",
                    )
                )

    # 2. Check collections / franchises
    col_conditions = [
        CollectionModel.name.ilike(f"%{clean_query}%"),
        CollectionModel.slug.ilike(f"%{clean_query}%"),
    ]
    if word_wildcard and word_wildcard != f"%{clean_query}%":
        col_conditions.append(CollectionModel.name.ilike(word_wildcard))
    col_filter = or_(*col_conditions)
    col_query = (
        select(CollectionModel)
        .where(
            CollectionModel.is_active.is_(True),
            CollectionModel.items.any(),
            col_filter,
        )
        .limit(2)
    )
    col_res = await db.execute(col_query)
    for col in col_res.scalars().all():
        results.append(
            LiveSearchResultItem(
                id=col.id,
                title=col.name,
                original_title=None,
                code=col.slug,
                year=None,
                poster_url=col.poster_url,
                imdb_rating=None,
                type="collection",
                extra="To'plam / Xronologiya",
            )
        )

    # 3. Search Movies
    movie_conditions = [
        MovieModel.title.ilike(f"%{clean_query}%"),
        MovieModel.original_title.ilike(f"%{clean_query}%"),
    ]
    if word_wildcard and word_wildcard != f"%{clean_query}%":
        movie_conditions.append(MovieModel.title.ilike(word_wildcard))
        movie_conditions.append(MovieModel.original_title.ilike(word_wildcard))
    is_potential_code = (
        " " not in code_query
        and len(code_query) <= 8
        and (code_query.isdigit() or code_query.isupper() or code_query.lower().startswith("s_"))
    )

    if is_potential_code:
        movie_conditions.append(MovieModel.code.ilike(f"%{code_query}%"))
        movie_conditions.append(MovieModel.short_code == code_query)
        if code_query.isdigit() and len(code_query) <= 9:
            movie_conditions.append(MovieModel.id == int(code_query))
    movie_filter = or_(*movie_conditions)

    # Order by starts_with first for natural ranking
    movie_order = case(
        (MovieModel.title.ilike(f"{clean_query}%"), 1),
        (MovieModel.original_title.ilike(f"{clean_query}%"), 2),
        else_=3,
    )
    movie_stmt = (
        select(MovieModel)
        .where(movie_filter)
        .order_by(movie_order, MovieModel.imdb_rating.desc().nullslast())
        .limit(limit)
    )
    movie_stmt = published_only(movie_stmt, MovieModel)
    if not include_adult:
        movie_stmt = exclude_adult_media(movie_stmt, MovieModel)
    movies_res = await db.execute(movie_stmt)
    for m in movies_res.scalars().all():
        if not any(r.id == m.id and r.type == "movie" for r in results):
            results.append(
                LiveSearchResultItem(
                    id=m.id,
                    title=m.title,
                    original_title=m.original_title,
                    code=m.code,
                    short_code=m.short_code,
                    year=m.release_year,
                    poster_url=m.poster_url,
                    imdb_rating=m.imdb_rating,
                    type="movie",
                )
            )

    # 4. Search Series
    series_conditions = [
        SeriesModel.title.ilike(f"%{clean_query}%"),
    ]
    if word_wildcard and word_wildcard != f"%{clean_query}%":
        series_conditions.append(SeriesModel.title.ilike(word_wildcard))
    if code_query and code_query != clean_query:
        series_conditions.append(SeriesModel.title.ilike(f"%{code_query}%"))
    if series_id_target:
        series_conditions.append(SeriesModel.id == series_id_target)
    series_filter = or_(*series_conditions)

    series_stmt = (
        select(SeriesModel)
        .where(series_filter)
        .order_by(SeriesModel.imdb_rating.desc().nullslast())
        .limit(limit)
    )
    series_stmt = published_only(series_stmt, SeriesModel)
    if not include_adult:
        series_stmt = exclude_adult_media(series_stmt, SeriesModel)
    series_res = await db.execute(series_stmt)
    for s in series_res.scalars().all():
        if not any(r.id == s.id and r.type == "series" for r in results):
            results.append(
                LiveSearchResultItem(
                    id=s.id,
                    title=s.title,
                    original_title=None,
                    code=f"s_{s.id}",
                    year=s.release_year,
                    poster_url=s.poster_url,
                    imdb_rating=s.imdb_rating,
                    type="series",
                )
            )

    # Trim to limit
    trimmed_results = results[:limit]
    response = LiveSearchResponse(query=clean_query, total=len(trimmed_results), results=trimmed_results)

    # Cache for 120 seconds
    response_data = response.model_dump(mode="json")
    await set_cache(cache_key, response_data, 120)

    return response
