"""
Content Lookup API endpoints (Admin only).
Allows searching TMDb and fetching movie/series metadata.
"""
from typing import Any, Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_current_admin, get_db_session
from app.api.limiter import limiter
from app.infrastructure.external.tmdb_client import tmdb_client
from app.infrastructure.external.translator import translator_service
from app.infrastructure.external.genre_mapper import map_tmdb_genres
from app.infrastructure.db.models.category import CategoryModel

router = APIRouter(prefix="/content-lookup", tags=["content-lookup"])


@router.get("/search")
@limiter.limit("30/minute")
async def search_content(
    request: Request,
    q: str | None = Query(None, description="Movie or series title to search"),
    query: str | None = Query(None, description="Alias for q"),
    type: Literal["movie", "tv", "series"] | None = Query(None, description="Type of content: movie or tv/series"),
    content_type: Literal["movie", "tv", "series"] | None = Query(None, description="Alias for type"),
    admin: dict = Depends(get_current_admin),
) -> list[dict[str, Any]]:
    """Search for movies or TV series on TMDb."""
    if not tmdb_client.api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TMDb API kaliti serverda sozlanmagan (backend/.env faylida TMDB_API_KEY ko'rsatilib, backend qayta ishga tushirilishi kerak).",
        )

    search_query = (q or query or "").strip()
    if not search_query:
        return []
    ctype = content_type or type or "movie"
    endpoint_type = "tv" if ctype in ("tv", "series") else "movie"
    results = await tmdb_client.search(query=search_query, content_type=endpoint_type)
    return results


@router.get("/details/{content_type}/{tmdb_id}")
@limiter.limit("30/minute")
async def get_content_details(
    request: Request,
    content_type: Literal["movie", "tv", "series"],
    tmdb_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
) -> dict[str, Any]:
    """Fetch complete metadata for a movie or series from TMDb, with Uzbek translation."""
    if not tmdb_client.api_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TMDb API kaliti serverda sozlanmagan (backend/.env faylida TMDB_API_KEY ko'rsatilishi kerak).",
        )

    ctype = "tv" if content_type in ("tv", "series") else "movie"
    details = await tmdb_client.get_details(tmdb_id=tmdb_id, content_type=ctype)
    if not details:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="TMDb ma'lumotlari topilmadi yoki xizmat vaqtincha javob bermayapti.",
        )

    # 1. Translate overview to Uzbek
    raw_overview = details.get("overview") or ""
    translated_desc, is_translated = await translator_service.translate_to_uzbek(raw_overview)
    details["description"] = translated_desc
    details["is_translated"] = is_translated

    # 2. Translate title to Uzbek
    raw_title = details.get("title") or ""
    orig_title = details.get("original_title") or ""
    translated_title, is_title_translated = await translator_service.translate_title_to_uzbek(raw_title, orig_title)
    details["uz_title"] = translated_title or raw_title
    details["raw_title"] = raw_title
    details["original_title"] = orig_title
    details["title"] = translated_title if translated_title else raw_title
    details["is_title_translated"] = is_title_translated

    # 2. Map genres to Uzbek
    uz_genres = map_tmdb_genres(details.get("genres_raw", []))
    details["genres"] = ", ".join(uz_genres) if uz_genres else details.get("genres_str", "")

    # 3. Match category IDs from database
    suggested_category_ids: list[int] = []
    if uz_genres:
        try:
            stmt = select(CategoryModel.id, CategoryModel.name)
            res = await db.execute(stmt)
            for cat_id, cat_name in res.all():
                if cat_name in uz_genres:
                    suggested_category_ids.append(cat_id)
        except Exception:
            pass
    details["suggested_category_ids"] = suggested_category_ids

    return details


@router.get("/duplicates")
@limiter.limit("60/minute")
async def check_duplicates(
    request: Request,
    title: str = Query(..., min_length=1, description="Title to search for duplicates"),
    tmdb_id: int | None = Query(None, description="TMDb ID to check exact match"),
    original_title: str | None = Query(None, description="Original title to check"),
    year: int | None = Query(None, description="Release year"),
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
) -> dict[str, list[dict[str, Any]]]:
    """Check database for exact and similar existing movies or series."""
    from sqlalchemy import or_
    from app.infrastructure.db.models.movie import MovieModel
    from app.infrastructure.db.models.series import SeriesModel

    exact_matches: list[dict[str, Any]] = []
    similar_matches: list[dict[str, Any]] = []
    exact_movie_ids: set[int] = set()
    exact_series_ids: set[int] = set()

    # 1. Exact match by tmdb_id
    if tmdb_id:
        m_stmt = select(MovieModel).where(MovieModel.tmdb_id == tmdb_id)
        m_res = await db.execute(m_stmt)
        for m in m_res.scalars().all():
            exact_matches.append({
                "type": "movie",
                "id": m.id,
                "title": m.title,
                "code": m.code,
                "release_year": m.release_year,
                "tmdb_id": m.tmdb_id,
                "match_reason": "tmdb_id",
            })
            exact_movie_ids.add(m.id)

        s_stmt = select(SeriesModel).where(SeriesModel.tmdb_id == tmdb_id)
        s_res = await db.execute(s_stmt)
        for s in s_res.scalars().all():
            exact_matches.append({
                "type": "series",
                "id": s.id,
                "title": s.title,
                "code": f"s_{s.id}",
                "release_year": s.release_year,
                "tmdb_id": s.tmdb_id,
                "match_reason": "tmdb_id",
            })
            exact_series_ids.add(s.id)

    # 2. Similar matches by title or original_title
    clean_title = title.strip()
    title_terms = [clean_title]
    if original_title and original_title.strip() and original_title.strip().lower() != clean_title.lower():
        title_terms.append(original_title.strip())

    # Search in movies
    movie_conds = []
    for t in title_terms:
        movie_conds.append(MovieModel.title.ilike(f"%{t}%"))
        movie_conds.append(MovieModel.original_title.ilike(f"%{t}%"))

    sim_m_stmt = select(MovieModel).where(or_(*movie_conds)).limit(10)
    sim_m_res = await db.execute(sim_m_stmt)
    for m in sim_m_res.scalars().all():
        if m.id not in exact_movie_ids:
            is_exact_title = (
                m.title.lower() == clean_title.lower()
                or (m.original_title and m.original_title.lower() == clean_title.lower())
            )
            item = {
                "type": "movie",
                "id": m.id,
                "title": m.title,
                "code": m.code,
                "release_year": m.release_year,
                "tmdb_id": m.tmdb_id,
                "match_reason": "exact_title" if is_exact_title else "similar_title",
            }
            if is_exact_title and not tmdb_id:
                exact_matches.append(item)
                exact_movie_ids.add(m.id)
            else:
                similar_matches.append(item)

    # Search in series
    series_conds = []
    for t in title_terms:
        series_conds.append(SeriesModel.title.ilike(f"%{t}%"))

    sim_s_stmt = select(SeriesModel).where(or_(*series_conds)).limit(10)
    sim_s_res = await db.execute(sim_s_stmt)
    for s in sim_s_res.scalars().all():
        if s.id not in exact_series_ids:
            is_exact_title = s.title.lower() == clean_title.lower()
            item = {
                "type": "series",
                "id": s.id,
                "title": s.title,
                "code": f"s_{s.id}",
                "release_year": s.release_year,
                "tmdb_id": s.tmdb_id,
                "match_reason": "exact_title" if is_exact_title else "similar_title",
            }
            if is_exact_title and not tmdb_id:
                exact_matches.append(item)
                exact_series_ids.add(s.id)
            else:
                similar_matches.append(item)

    return {
        "exact": exact_matches,
        "similar": similar_matches,
    }
