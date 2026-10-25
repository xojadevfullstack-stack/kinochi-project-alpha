"""
API v1 — Content Requests & External Movie/Series Search.
Allows users to search TMDB & Kinopoisk for movies/series not currently in the platform,
and submit requests (buyurtmalar) for admins to add them.
"""
import logging
from typing import Literal
import httpx
from fastapi import APIRouter, Depends, Query, Request, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select, or_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session
from app.api.limiter import limiter
from app.core.config import settings
from app.core.cache import get_cache, set_cache
from app.infrastructure.db.models.content_request import ContentRequestModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel
from app.infrastructure.external.tmdb_client import TMDbClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content-requests", tags=["content-requests"])


# ── Pydantic Schemas ──────────────────────────────────────────────────

class ExternalSearchResultItem(BaseModel):
    tmdb_id: int | None = None
    kinopoisk_id: int | None = None
    title: str
    original_title: str | None = None
    media_type: Literal["movie", "series"] = "movie"
    release_year: int | None = None
    poster_url: str | None = None
    overview: str | None = None
    vote_average: float | None = None
    in_library: bool = False
    library_code: str | None = None  # movie code or s_{series_id}
    library_id: int | None = None
    request_count: int = 0
    is_requested: bool = False


class ExternalSearchResponse(BaseModel):
    query: str
    total: int
    results: list[ExternalSearchResultItem]


class ContentRequestCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    original_title: str | None = Field(None, max_length=255)
    media_type: Literal["movie", "series"] = "movie"
    release_year: int | None = None
    poster_url: str | None = Field(None, max_length=1024)
    overview: str | None = None
    tmdb_id: int | None = None
    kinopoisk_id: int | None = None
    preferred_language: Literal["uz", "ru", "sub", "any"] = "uz"
    user_contact: str | None = Field(None, max_length=255)
    telegram_user_id: int | None = None


class ContentRequestResponse(BaseModel):
    id: int
    title: str
    original_title: str | None = None
    media_type: str
    release_year: int | None = None
    poster_url: str | None = None
    overview: str | None = None
    tmdb_id: int | None = None
    kinopoisk_id: int | None = None
    preferred_language: str
    vote_count: int
    status: str
    created_at: str

    class Config:
        from_attributes = True


class ContentRequestListResponse(BaseModel):
    total: int
    items: list[ContentRequestResponse]


# ── Helper for Kinopoisk Search ───────────────────────────────────────

async def search_kinopoisk(query: str, limit: int = 5) -> list[dict]:
    """Search Kinopoisk Unofficial API if API key is configured."""
    kp_key = getattr(settings, "KINOPOISK_API_KEY", "").strip()
    if not kp_key:
        return []

    cache_key = f"cache:kp:search:{query.lower()}"
    cached = await get_cache(cache_key)
    if cached is not None:
        return cached

    url = "https://kinopoiskapiunofficial.tech/api/v2.1/films/search-by-keyword"
    headers = {"X-API-KEY": kp_key, "Accept": "application/json"}
    params = {"keyword": query, "page": 1}

    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                films = data.get("films", [])[:limit]
                results = []
                for f in films:
                    film_id = f.get("filmId")
                    title = f.get("nameRu") or f.get("nameEn") or "Nomsiz"
                    year_raw = f.get("year")
                    try:
                        year = int(year_raw) if year_raw and str(year_raw).isdigit() else None
                    except Exception:
                        year = None
                    results.append({
                        "kinopoisk_id": film_id,
                        "title": title,
                        "original_title": f.get("nameEn"),
                        "media_type": "series" if "сериал" in str(f.get("description", "")).lower() else "movie",
                        "release_year": year,
                        "poster_url": f.get("posterUrlPreview") or f.get("posterUrl"),
                        "overview": f.get("description"),
                        "vote_average": float(f.get("rating")) if f.get("rating") and str(f.get("rating")).replace(".", "", 1).isdigit() else None,
                    })
                await set_cache(cache_key, results, 300)
                return results
    except Exception as e:
        logger.warning(f"Kinopoisk search failed: {e}")
    return []


# ── Endpoints ─────────────────────────────────────────────────────────

@router.get("/external-search", response_model=ExternalSearchResponse)
@limiter.limit("60/minute")
async def external_search(
    request: Request,
    q: str = Query(..., min_length=1, max_length=100, description="Kino yoki serial nomi"),
    media_type: Literal["all", "movie", "series"] = Query("all", description="Kontent turi"),
    limit: int = Query(15, ge=1, le=30),
    db: AsyncSession = Depends(get_db_session),
):
    """
    Search TMDB & Kinopoisk databases for movies/series.
    Cross-checks with local database to see if already present in library,
    and returns vote/request status so users can request missing ones.
    """
    clean_q = q.strip()
    if not clean_q:
        return ExternalSearchResponse(query=q, total=0, results=[])

    cache_key = f"cache:ext_search:{media_type}:{clean_q.lower()}:{limit}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    tmdb = TMDbClient()
    raw_results: list[dict] = []

    # 1. TMDB Search
    try:
        if media_type in ("all", "movie"):
            movie_res = await tmdb.search(clean_q, content_type="movie")
            for m in movie_res[:limit]:
                raw_results.append({
                    "tmdb_id": m.get("tmdb_id") or m.get("id"),
                    "title": m.get("title") or "Nomsiz",
                    "original_title": m.get("original_title"),
                    "media_type": "movie",
                    "release_year": m.get("release_year"),
                    "poster_url": m.get("poster_url"),
                    "overview": m.get("overview"),
                    "vote_average": m.get("vote_average"),
                })

        if media_type in ("all", "series"):
            tv_res = await tmdb.search(clean_q, content_type="tv")
            for t in tv_res[:limit]:
                raw_results.append({
                    "tmdb_id": t.get("tmdb_id") or t.get("id"),
                    "title": t.get("title") or "Nomsiz",
                    "original_title": t.get("original_title"),
                    "media_type": "series",
                    "release_year": t.get("release_year"),
                    "poster_url": t.get("poster_url"),
                    "overview": t.get("overview"),
                    "vote_average": t.get("vote_average"),
                })
    except Exception as e:
        logger.error(f"Error querying TMDB for external search: {e}", exc_info=True)

    # 2. Kinopoisk Search if needed
    if len(raw_results) < 5:
        kp_res = await search_kinopoisk(clean_q, limit=5)
        for kp in kp_res:
            # avoid duplicates if title matches
            if not any(r["title"].lower() == kp["title"].lower() for r in raw_results):
                raw_results.append(kp)

    if not raw_results:
        res = ExternalSearchResponse(query=clean_q, total=0, results=[])
        return res

    # 3. Cross-reference with internal database
    tmdb_ids = [r["tmdb_id"] for r in raw_results if r.get("tmdb_id")]

    # Check movies
    local_movies_map: dict[int, MovieModel] = {}
    if tmdb_ids:
        m_stmt = select(MovieModel).where(MovieModel.tmdb_id.in_(tmdb_ids))
        m_res = await db.execute(m_stmt)
        for m in m_res.scalars().all():
            if m.tmdb_id:
                local_movies_map[m.tmdb_id] = m

    # Check series
    local_series_map: dict[int, SeriesModel] = {}
    if tmdb_ids:
        s_stmt = select(SeriesModel).where(SeriesModel.tmdb_id.in_(tmdb_ids))
        s_res = await db.execute(s_stmt)
        for s in s_res.scalars().all():
            if s.tmdb_id:
                local_series_map[s.tmdb_id] = s

    # Check existing user requests
    requests_map: dict[int, ContentRequestModel] = {}
    if tmdb_ids:
        req_stmt = select(ContentRequestModel).where(
            ContentRequestModel.tmdb_id.in_(tmdb_ids),
            ContentRequestModel.status.in_(["pending", "in_review"]),
        )
        req_res = await db.execute(req_stmt)
        for req_item in req_res.scalars().all():
            if req_item.tmdb_id:
                requests_map[req_item.tmdb_id] = req_item

    # Build final items
    final_items: list[ExternalSearchResultItem] = []
    seen_unique: set[str] = set()

    for item in raw_results:
        t_id = item.get("tmdb_id")
        m_type = item.get("media_type", "movie")
        u_key = f"{m_type}:{t_id or item.get('title')}"
        if u_key in seen_unique:
            continue
        seen_unique.add(u_key)

        in_lib = False
        lib_code = None
        lib_id = None

        if t_id and m_type == "movie" and t_id in local_movies_map:
            in_lib = True
            lib_code = local_movies_map[t_id].code
            lib_id = local_movies_map[t_id].id
        elif t_id and m_type == "series" and t_id in local_series_map:
            in_lib = True
            lib_code = f"s_{local_series_map[t_id].id}"
            lib_id = local_series_map[t_id].id

        req_count = 0
        is_req = False
        if t_id and t_id in requests_map:
            req_count = requests_map[t_id].vote_count
            is_req = True

        final_items.append(
            ExternalSearchResultItem(
                tmdb_id=t_id,
                kinopoisk_id=item.get("kinopoisk_id"),
                title=item.get("title") or "Nomsiz",
                original_title=item.get("original_title"),
                media_type=m_type,
                release_year=item.get("release_year"),
                poster_url=item.get("poster_url"),
                overview=item.get("overview"),
                vote_average=item.get("vote_average"),
                in_library=in_lib,
                library_code=lib_code,
                library_id=lib_id,
                request_count=req_count,
                is_requested=is_req,
            )
        )

    response = ExternalSearchResponse(
        query=clean_q,
        total=len(final_items),
        results=final_items[:limit],
    )

    # Cache for 2 minutes
    await set_cache(cache_key, response.model_dump(mode="json"), 120)
    return response


@router.post("", status_code=status.HTTP_201_CREATED)
@limiter.limit("15/minute")
async def create_or_vote_content_request(
    request: Request,
    payload: ContentRequestCreate,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Submit a request to add a missing movie or series.
    If the movie is already requested, increments the vote count.
    """
    clean_title = payload.title.strip()
    if not clean_title:
        raise HTTPException(status_code=400, detail="Film yoki serial nomi kiritilishi shart")

    # Check IP
    ip = request.client.host if request.client else None

    # Check if this item is already requested and pending/in_review
    existing_request: ContentRequestModel | None = None

    if payload.tmdb_id:
        stmt = select(ContentRequestModel).where(
            ContentRequestModel.tmdb_id == payload.tmdb_id,
            ContentRequestModel.media_type == payload.media_type,
            ContentRequestModel.status.in_(["pending", "in_review"]),
        ).limit(1)
        res = await db.execute(stmt)
        existing_request = res.scalar_one_or_none()

    if not existing_request:
        # Check by exact title and year
        conditions = [func.lower(ContentRequestModel.title) == clean_title.lower()]
        if payload.release_year:
            conditions.append(ContentRequestModel.release_year == payload.release_year)
        conditions.append(ContentRequestModel.media_type == payload.media_type)
        conditions.append(ContentRequestModel.status.in_(["pending", "in_review"]))

        stmt = select(ContentRequestModel).where(*conditions).limit(1)
        res = await db.execute(stmt)
        existing_request = res.scalar_one_or_none()

    if existing_request:
        existing_request.vote_count += 1
        if payload.user_contact and not existing_request.user_contact:
            existing_request.user_contact = payload.user_contact
        if payload.telegram_user_id and not existing_request.telegram_user_id:
            existing_request.telegram_user_id = payload.telegram_user_id
        await db.commit()
        await db.refresh(existing_request)
        return {
            "success": True,
            "message": f"Bu kontent avval so'ralgan! Ovozlar soni {existing_request.vote_count} taga yetdi.",
            "request_id": existing_request.id,
            "vote_count": existing_request.vote_count,
            "is_new": False,
        }

    # Create new request
    new_request = ContentRequestModel(
        title=clean_title,
        original_title=payload.original_title,
        media_type=payload.media_type,
        release_year=payload.release_year,
        poster_url=payload.poster_url,
        overview=payload.overview,
        tmdb_id=payload.tmdb_id,
        kinopoisk_id=payload.kinopoisk_id,
        preferred_language=payload.preferred_language,
        user_contact=payload.user_contact,
        telegram_user_id=payload.telegram_user_id,
        ip_address=ip,
        vote_count=1,
        status="pending",
    )
    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)

    return {
        "success": True,
        "message": "So'rovingiz muvaffaqiyatli qabul qilindi! Tez orada platformaga qo'shish choralari ko'riladi.",
        "request_id": new_request.id,
        "vote_count": new_request.vote_count,
        "is_new": True,
    }


@router.get("", response_model=ContentRequestListResponse)
@limiter.limit("60/minute")
async def list_content_requests(
    request: Request,
    status_filter: str | None = Query(None, alias="status"),
    sort: Literal["votes", "recent"] = Query("votes"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db_session),
):
    """
    List user movie & series requests.
    Supports sorting by most voted or most recent.
    """
    stmt = select(ContentRequestModel)
    if status_filter:
        stmt = stmt.where(ContentRequestModel.status == status_filter)
    else:
        stmt = stmt.where(ContentRequestModel.status.in_(["pending", "in_review"]))

    if sort == "votes":
        stmt = stmt.order_by(desc(ContentRequestModel.vote_count), desc(ContentRequestModel.created_at))
    else:
        stmt = stmt.order_by(desc(ContentRequestModel.created_at))

    # Total count
    count_stmt = select(func.count(ContentRequestModel.id))
    if status_filter:
        count_stmt = count_stmt.where(ContentRequestModel.status == status_filter)
    else:
        count_stmt = count_stmt.where(ContentRequestModel.status.in_(["pending", "in_review"]))

    total_res = await db.execute(count_stmt)
    total = total_res.scalar_one()

    # Paginate
    stmt = stmt.offset(offset).limit(limit)
    res = await db.execute(stmt)
    items = res.scalars().all()

    formatted_items = [
        ContentRequestResponse(
            id=item.id,
            title=item.title,
            original_title=item.original_title,
            media_type=item.media_type,
            release_year=item.release_year,
            poster_url=item.poster_url,
            overview=item.overview,
            tmdb_id=item.tmdb_id,
            kinopoisk_id=item.kinopoisk_id,
            preferred_language=item.preferred_language,
            vote_count=item.vote_count,
            status=item.status,
            created_at=item.created_at.isoformat() if item.created_at else "",
        )
        for item in items
    ]

    return ContentRequestListResponse(total=total, items=formatted_items)
