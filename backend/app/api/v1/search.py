"""
API v1 — Search endpoints.
Provides ultra-fast debounced live search for website autocomplete and Telegram bot.
"""
from typing import Literal
from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy import select, or_, func, case
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.api.limiter import limiter
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel
from app.infrastructure.db.models.collection import CollectionModel
from app.infrastructure.db.query_filters import published_only
from app.core.cache import get_cache, set_cache

router = APIRouter(prefix="/search", tags=["search"])


class LiveSearchResultItem(BaseModel):
    id: int
    title: str
    original_title: str | None = None
    code: str
    year: int | None = None
    poster_url: str | None = None
    imdb_rating: float | None = None
    type: Literal["movie", "series", "collection"]
    extra: str | None = None


class LiveSearchResponse(BaseModel):
    query: str
    total: int
    results: list[LiveSearchResultItem]


@router.get("/live", response_model=LiveSearchResponse)
@limiter.limit("180/minute")
async def live_search(
    request: Request,
    q: str = Query(..., min_length=1, description="Qidiruv matni yoki kod"),
    limit: int = Query(8, ge=1, le=20, description="Natijalar soni"),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Live autocomplete search endpoint.
    Searches across movies, series, and franchises with instant response time.
    """
    clean_query = q.strip()
    if not clean_query:
        return LiveSearchResponse(query=q, total=0, results=[])

    cache_key = f"cache:search:live:{clean_query.lower()}:{limit}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    results: list[LiveSearchResultItem] = []

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
        # Check movie code or ID
        movie_code_conditions = [MovieModel.code.ilike(code_query)]
        if code_query.isdigit():
            movie_code_conditions.append(MovieModel.id == int(code_query))
        movie_code_stmt = published_only(
            select(MovieModel).where(or_(*movie_code_conditions)).limit(1), MovieModel
        )
        movie_code_res = await db.execute(movie_code_stmt)
        movie_by_code = movie_code_res.scalar_one_or_none()
        if movie_by_code:
            results.append(
                LiveSearchResultItem(
                    id=movie_by_code.id,
                    title=movie_by_code.title,
                    original_title=movie_by_code.original_title,
                    code=movie_by_code.code,
                    year=movie_by_code.release_year,
                    poster_url=movie_by_code.poster_url,
                    imdb_rating=movie_by_code.imdb_rating,
                    type="movie",
                    extra="Kod bo'yicha topildi",
                )
            )

        if series_id_target:
            series_by_id_stmt = published_only(
                select(SeriesModel).where(SeriesModel.id == series_id_target).limit(1), SeriesModel
            )
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
    col_filter = or_(
        CollectionModel.name.ilike(f"%{clean_query}%"),
        CollectionModel.slug.ilike(f"%{clean_query}%"),
    )
    col_query = (
        select(CollectionModel)
        .where(
            CollectionModel.is_active == True,
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
    is_potential_code = (
        " " not in code_query
        and len(code_query) <= 8
        and (code_query.isdigit() or code_query.isupper() or code_query.lower().startswith("s_"))
    )

    if is_potential_code:
        movie_conditions.append(MovieModel.code.ilike(f"%{code_query}%"))
        if code_query.isdigit():
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
    movies_res = await db.execute(movie_stmt)
    for m in movies_res.scalars().all():
        if not any(r.id == m.id and r.type == "movie" for r in results):
            results.append(
                LiveSearchResultItem(
                    id=m.id,
                    title=m.title,
                    original_title=m.original_title,
                    code=m.code,
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
