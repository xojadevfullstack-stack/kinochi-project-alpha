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

    # 1. Check if user typed a movie code (e.g., "#BYVC33" or "BYVC33" or "s_30")
    code_query = clean_query.lstrip("#").upper()
    if len(code_query) >= 2:
        # Check movie code
        movie_code_res = await db.execute(
            select(MovieModel).where(MovieModel.code == code_query).limit(1)
        )
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

    # 2. Check collections / franchises
    col_filter = or_(
        CollectionModel.name.ilike(f"%{clean_query}%"),
        CollectionModel.slug.ilike(f"%{clean_query}%"),
    )
    col_query = (
        select(CollectionModel)
        .where(CollectionModel.is_active == True, col_filter)
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
    movie_filter = or_(
        MovieModel.title.ilike(f"%{clean_query}%"),
        MovieModel.original_title.ilike(f"%{clean_query}%"),
        MovieModel.code.ilike(f"%{clean_query}%"),
    )
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
    series_filter = or_(
        SeriesModel.title.ilike(f"%{clean_query}%"),
    )
    series_stmt = (
        select(SeriesModel)
        .where(series_filter)
        .order_by(SeriesModel.imdb_rating.desc().nullslast())
        .limit(limit)
    )
    series_res = await db.execute(series_stmt)
    for s in series_res.scalars().all():
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
