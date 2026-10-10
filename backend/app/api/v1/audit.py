"""
API v1 — Content Audit & Quality Control endpoints (Admin only).
Allows auditing, filtering, quick-editing and auto-fixing movies and series with data issues.
"""
import logging
from typing import Literal, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_, not_
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_admin, get_db_session
from app.api.limiter import limiter
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.models.translation import MovieTranslationModel, EpisodeTranslationModel
from app.infrastructure.db.models.category import CategoryModel
from app.infrastructure.external.tmdb_client import tmdb_client
from app.infrastructure.external.translator import translator_service
from app.infrastructure.external.genre_mapper import map_tmdb_genres
from app.core.cache import delete_cache_pattern

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/audit", tags=["audit"])


# ── Schemas ──────────────────────────────────────────────────────

class IssueBadge(BaseModel):
    code: str
    label: str
    severity: Literal["danger", "warning", "info"]

class AuditItemResponse(BaseModel):
    id: int
    content_type: Literal["movie", "series"]
    title: str
    original_title: str | None = None
    code: str | None = None
    poster_url: str | None = None
    trailer_url: str | None = None
    description: str | None = None
    genres: str | None = None
    release_year: int | None = None
    imdb_rating: float | None = None
    tmdb_id: int | None = None
    source_id: int | None = None
    source_topic_id: int | None = None
    categories: list[dict[str, Any]] = []
    
    # Flags
    has_video: bool
    has_poster: bool
    has_description: bool
    has_genres: bool
    has_categories: bool
    has_trailer: bool
    has_tmdb: bool
    has_source: bool
    
    issues: list[IssueBadge] = []
    issues_count: int = 0

class AuditStatsSection(BaseModel):
    total: int
    missing_video: int
    missing_poster: int
    missing_description: int
    missing_genres: int
    missing_categories: int
    missing_trailer: int
    missing_tmdb: int
    missing_source: int
    has_any_issue: int
    healthy_count: int
    health_score: float

class AuditStatsResponse(BaseModel):
    movies: AuditStatsSection
    series: AuditStatsSection
    overall_health_score: float
    total_content: int
    total_issues_content: int

class QuickUpdatePayload(BaseModel):
    title: str | None = None
    original_title: str | None = None
    description: str | None = None
    poster_url: str | None = None
    trailer_url: str | None = None
    genres: str | None = None
    release_year: int | None = None
    imdb_rating: float | None = None
    tmdb_id: int | None = None
    category_ids: list[int] | None = None


# ── Helpers for Filtering ────────────────────────────────────────

def get_movie_issue_condition(issue_type: str):
    has_valid_video = MovieModel.translations.any(
        MovieTranslationModel.telegram_file_id.isnot(None) & (MovieTranslationModel.telegram_file_id != "")
    )
    has_valid_poster = MovieModel.poster_url.isnot(None) & (MovieModel.poster_url != "") & MovieModel.poster_url.ilike("http%")
    has_valid_desc = MovieModel.description.isnot(None) & (MovieModel.description != "") & (func.length(MovieModel.description) >= 30)
    has_valid_genres = MovieModel.genres.isnot(None) & (MovieModel.genres != "")
    has_valid_cat = MovieModel.categories.any()
    has_valid_trailer = MovieModel.trailer_url.isnot(None) & (MovieModel.trailer_url != "")
    has_valid_tmdb = MovieModel.tmdb_id.isnot(None) & (MovieModel.tmdb_id != 0)
    has_valid_source = MovieModel.source_topic_id.isnot(None)

    if issue_type == "missing_video":
        return not_(has_valid_video)
    elif issue_type == "missing_poster":
        return not_(has_valid_poster)
    elif issue_type == "missing_description":
        return not_(has_valid_desc)
    elif issue_type == "missing_genres":
        return not_(has_valid_genres)
    elif issue_type == "missing_categories":
        return not_(has_valid_cat)
    elif issue_type == "missing_trailer":
        return not_(has_valid_trailer)
    elif issue_type == "missing_tmdb":
        return not_(has_valid_tmdb)
    elif issue_type == "missing_source":
        return not_(has_valid_source)
    elif issue_type == "healthy":
        return and_(has_valid_video, has_valid_poster, has_valid_desc, has_valid_genres, has_valid_cat)
    elif issue_type == "all_issues":
        return or_(
            not_(has_valid_video),
            not_(has_valid_poster),
            not_(has_valid_desc),
            not_(has_valid_genres),
            not_(has_valid_cat),
            not_(has_valid_trailer),
            not_(has_valid_tmdb),
        )
    return None

def get_series_issue_condition(issue_type: str):
    # Valid video: has seasons AND none of its seasons is empty AND none of its episodes is missing video
    has_seasons = SeriesModel.seasons.any()
    has_empty_seasons = SeriesModel.seasons.any(~SeasonModel.episodes.any())
    has_episodes_without_vid = SeriesModel.seasons.any(
        SeasonModel.episodes.any(
            ~EpisodeModel.translations.any(
                EpisodeTranslationModel.telegram_file_id.isnot(None) & (EpisodeTranslationModel.telegram_file_id != "")
            )
        )
    )
    # A series is missing video if no seasons, or has empty season, or has episode without video
    is_missing_video = or_(not_(has_seasons), has_empty_seasons, has_episodes_without_vid)

    has_valid_poster = SeriesModel.poster_url.isnot(None) & (SeriesModel.poster_url != "") & SeriesModel.poster_url.ilike("http%")
    has_valid_desc = SeriesModel.description.isnot(None) & (SeriesModel.description != "") & (func.length(SeriesModel.description) >= 30)
    has_valid_cat = SeriesModel.categories.any()
    has_valid_trailer = SeriesModel.trailer_url.isnot(None) & (SeriesModel.trailer_url != "")
    has_valid_tmdb = SeriesModel.tmdb_id.isnot(None) & (SeriesModel.tmdb_id != 0)
    has_valid_source = SeriesModel.source_id.isnot(None)

    if issue_type == "missing_video":
        return is_missing_video
    elif issue_type == "missing_poster":
        return not_(has_valid_poster)
    elif issue_type == "missing_description":
        return not_(has_valid_desc)
    elif issue_type == "missing_genres":
        # Series don't have separate genres field, using categories
        return not_(has_valid_cat)
    elif issue_type == "missing_categories":
        return not_(has_valid_cat)
    elif issue_type == "missing_trailer":
        return not_(has_valid_trailer)
    elif issue_type == "missing_tmdb":
        return not_(has_valid_tmdb)
    elif issue_type == "missing_source":
        return not_(has_valid_source)
    elif issue_type == "healthy":
        return and_(not_(is_missing_video), has_valid_poster, has_valid_desc, has_valid_cat)
    elif issue_type == "all_issues":
        return or_(
            is_missing_video,
            not_(has_valid_poster),
            not_(has_valid_desc),
            not_(has_valid_cat),
            not_(has_valid_trailer),
            not_(has_valid_tmdb),
        )
    return None


def evaluate_movie_issues(movie: MovieModel) -> tuple[dict[str, bool], list[IssueBadge]]:
    has_video = any(
        t.telegram_file_id and str(t.telegram_file_id).strip() != ""
        for t in (movie.translations or [])
    )
    has_poster = bool(movie.poster_url and movie.poster_url.strip().startswith("http"))
    has_desc = bool(movie.description and len(movie.description.strip()) >= 30)
    has_genres = bool(movie.genres and movie.genres.strip() != "")
    has_categories = bool(movie.categories and len(movie.categories) > 0)
    has_trailer = bool(movie.trailer_url and movie.trailer_url.strip() != "")
    has_tmdb = bool(movie.tmdb_id and movie.tmdb_id > 0)
    has_source = bool(movie.source_topic_id is not None)

    flags = {
        "has_video": has_video,
        "has_poster": has_poster,
        "has_description": has_desc,
        "has_genres": has_genres,
        "has_categories": has_categories,
        "has_trailer": has_trailer,
        "has_tmdb": has_tmdb,
        "has_source": has_source,
    }

    issues: list[IssueBadge] = []
    if not has_video:
        issues.append(IssueBadge(code="missing_video", label="Videosi yo'q", severity="danger"))
    if not has_poster:
        issues.append(IssueBadge(code="missing_poster", label="Posteri yo'q", severity="danger"))
    if not has_desc:
        issues.append(IssueBadge(code="missing_description", label="Tasnifi yo'q / qisqa", severity="warning"))
    if not has_genres:
        issues.append(IssueBadge(code="missing_genres", label="Janrlari yo'q", severity="warning"))
    if not has_categories:
        issues.append(IssueBadge(code="missing_categories", label="Kategoriya yo'q", severity="warning"))
    if not has_trailer:
        issues.append(IssueBadge(code="missing_trailer", label="Treyler yo'q", severity="info"))
    if not has_tmdb:
        issues.append(IssueBadge(code="missing_tmdb", label="TMDb ulanmagan", severity="info"))
    if not has_source:
        issues.append(IssueBadge(code="missing_source", label="Topic ochilmagan", severity="info"))

    return flags, issues


def evaluate_series_issues(s: SeriesModel) -> tuple[dict[str, bool], list[IssueBadge]]:
    seasons = s.seasons or []
    has_seasons = len(seasons) > 0
    all_episodes = [ep for sz in seasons for ep in (sz.episodes or [])]
    has_episodes = len(all_episodes) > 0
    
    # All episodes must have at least one translation with valid telegram_file_id
    has_video = (
        has_seasons
        and has_episodes
        and all(
            any(t.telegram_file_id and str(t.telegram_file_id).strip() != "" for t in (ep.translations or []))
            for ep in all_episodes
        )
    )

    has_poster = bool(s.poster_url and s.poster_url.strip().startswith("http"))
    has_desc = bool(s.description and len(s.description.strip()) >= 30)
    has_categories = bool(s.categories and len(s.categories) > 0)
    has_trailer = bool(s.trailer_url and s.trailer_url.strip() != "")
    has_tmdb = bool(s.tmdb_id and s.tmdb_id > 0)
    has_source = bool(s.source_id is not None)

    flags = {
        "has_video": has_video,
        "has_poster": has_poster,
        "has_description": has_desc,
        "has_genres": has_categories, # Series use categories as genres
        "has_categories": has_categories,
        "has_trailer": has_trailer,
        "has_tmdb": has_tmdb,
        "has_source": has_source,
    }

    issues: list[IssueBadge] = []
    if not has_seasons:
        issues.append(IssueBadge(code="missing_video", label="Mavsumlari yo'q", severity="danger"))
    elif not has_episodes:
        issues.append(IssueBadge(code="missing_video", label="Qismlari yo'q", severity="danger"))
    elif not has_video:
        issues.append(IssueBadge(code="missing_video", label="Videosi chala", severity="danger"))

    if not has_poster:
        issues.append(IssueBadge(code="missing_poster", label="Posteri yo'q", severity="danger"))
    if not has_desc:
        issues.append(IssueBadge(code="missing_description", label="Tasnifi yo'q / qisqa", severity="warning"))
    if not has_categories:
        issues.append(IssueBadge(code="missing_categories", label="Kategoriya yo'q", severity="warning"))
    if not has_trailer:
        issues.append(IssueBadge(code="missing_trailer", label="Treyler yo'q", severity="info"))
    if not has_tmdb:
        issues.append(IssueBadge(code="missing_tmdb", label="TMDb ulanmagan", severity="info"))
    if not has_source:
        issues.append(IssueBadge(code="missing_source", label="Manba yo'q", severity="info"))

    return flags, issues


# ── Endpoints ────────────────────────────────────────────────────

@router.get("/stats", response_model=AuditStatsResponse)
@limiter.limit("60/minute")
async def get_audit_stats(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """Returns detailed quality audit counters for movies and series."""
    # --- Movies Stats ---
    total_m = await db.scalar(select(func.count(MovieModel.id))) or 0
    
    cond_no_vid_m = get_movie_issue_condition("missing_video")
    no_vid_m = (await db.scalar(select(func.count(MovieModel.id)).where(cond_no_vid_m))) or 0 if cond_no_vid_m is not None else 0

    cond_no_post_m = get_movie_issue_condition("missing_poster")
    no_post_m = (await db.scalar(select(func.count(MovieModel.id)).where(cond_no_post_m))) or 0 if cond_no_post_m is not None else 0

    cond_no_desc_m = get_movie_issue_condition("missing_description")
    no_desc_m = (await db.scalar(select(func.count(MovieModel.id)).where(cond_no_desc_m))) or 0 if cond_no_desc_m is not None else 0

    cond_no_gen_m = get_movie_issue_condition("missing_genres")
    no_gen_m = (await db.scalar(select(func.count(MovieModel.id)).where(cond_no_gen_m))) or 0 if cond_no_gen_m is not None else 0

    cond_no_cat_m = get_movie_issue_condition("missing_categories")
    no_cat_m = (await db.scalar(select(func.count(MovieModel.id)).where(cond_no_cat_m))) or 0 if cond_no_cat_m is not None else 0

    cond_no_tr_m = get_movie_issue_condition("missing_trailer")
    no_tr_m = (await db.scalar(select(func.count(MovieModel.id)).where(cond_no_tr_m))) or 0 if cond_no_tr_m is not None else 0

    cond_no_tmdb_m = get_movie_issue_condition("missing_tmdb")
    no_tmdb_m = (await db.scalar(select(func.count(MovieModel.id)).where(cond_no_tmdb_m))) or 0 if cond_no_tmdb_m is not None else 0

    cond_no_src_m = get_movie_issue_condition("missing_source")
    no_src_m = (await db.scalar(select(func.count(MovieModel.id)).where(cond_no_src_m))) or 0 if cond_no_src_m is not None else 0

    cond_any_m = get_movie_issue_condition("all_issues")
    any_m = (await db.scalar(select(func.count(MovieModel.id)).where(cond_any_m))) or 0 if cond_any_m is not None else 0

    healthy_m = max(0, total_m - any_m)
    health_score_m = round((healthy_m / total_m * 100), 1) if total_m > 0 else 100.0

    # --- Series Stats ---
    total_s = await db.scalar(select(func.count(SeriesModel.id))) or 0

    cond_no_vid_s = get_series_issue_condition("missing_video")
    no_vid_s = (await db.scalar(select(func.count(SeriesModel.id)).where(cond_no_vid_s))) or 0 if cond_no_vid_s is not None else 0

    cond_no_post_s = get_series_issue_condition("missing_poster")
    no_post_s = (await db.scalar(select(func.count(SeriesModel.id)).where(cond_no_post_s))) or 0 if cond_no_post_s is not None else 0

    cond_no_desc_s = get_series_issue_condition("missing_description")
    no_desc_s = (await db.scalar(select(func.count(SeriesModel.id)).where(cond_no_desc_s))) or 0 if cond_no_desc_s is not None else 0

    cond_no_cat_s = get_series_issue_condition("missing_categories")
    no_cat_s = (await db.scalar(select(func.count(SeriesModel.id)).where(cond_no_cat_s))) or 0 if cond_no_cat_s is not None else 0

    cond_no_tr_s = get_series_issue_condition("missing_trailer")
    no_tr_s = (await db.scalar(select(func.count(SeriesModel.id)).where(cond_no_tr_s))) or 0 if cond_no_tr_s is not None else 0

    cond_no_tmdb_s = get_series_issue_condition("missing_tmdb")
    no_tmdb_s = (await db.scalar(select(func.count(SeriesModel.id)).where(cond_no_tmdb_s))) or 0 if cond_no_tmdb_s is not None else 0

    cond_no_src_s = get_series_issue_condition("missing_source")
    no_src_s = (await db.scalar(select(func.count(SeriesModel.id)).where(cond_no_src_s))) or 0 if cond_no_src_s is not None else 0

    cond_any_s = get_series_issue_condition("all_issues")
    any_s = (await db.scalar(select(func.count(SeriesModel.id)).where(cond_any_s))) or 0 if cond_any_s is not None else 0

    healthy_s = max(0, total_s - any_s)
    health_score_s = round((healthy_s / total_s * 100), 1) if total_s > 0 else 100.0

    total_content = total_m + total_s
    total_issues = any_m + any_s
    total_healthy = healthy_m + healthy_s
    overall_score = round((total_healthy / total_content * 100), 1) if total_content > 0 else 100.0

    return AuditStatsResponse(
        movies=AuditStatsSection(
            total=total_m,
            missing_video=no_vid_m,
            missing_poster=no_post_m,
            missing_description=no_desc_m,
            missing_genres=no_gen_m,
            missing_categories=no_cat_m,
            missing_trailer=no_tr_m,
            missing_tmdb=no_tmdb_m,
            missing_source=no_src_m,
            has_any_issue=any_m,
            healthy_count=healthy_m,
            health_score=health_score_m,
        ),
        series=AuditStatsSection(
            total=total_s,
            missing_video=no_vid_s,
            missing_poster=no_post_s,
            missing_description=no_desc_s,
            missing_genres=no_cat_s,
            missing_categories=no_cat_s,
            missing_trailer=no_tr_s,
            missing_tmdb=no_tmdb_s,
            missing_source=no_src_s,
            has_any_issue=any_s,
            healthy_count=healthy_s,
            health_score=health_score_s,
        ),
        overall_health_score=overall_score,
        total_content=total_content,
        total_issues_content=total_issues,
    )


@router.get("/items")
@limiter.limit("60/minute")
async def list_audit_items(
    request: Request,
    content_type: Literal["movie", "series"] = Query("movie"),
    issue_type: str = Query("all_issues"),
    search: str | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """List movies or series filtered by specific data issue."""
    clean_search = (search or "").strip()

    if content_type == "movie":
        stmt = select(MovieModel).options(
            selectinload(MovieModel.categories),
            selectinload(MovieModel.translations),
        )

        issue_cond = get_movie_issue_condition(issue_type)
        if issue_cond is not None:
            stmt = stmt.where(issue_cond)

        if clean_search:
            search_cond = [
                MovieModel.title.ilike(f"%{clean_search}%"),
                MovieModel.code.ilike(f"%{clean_search}%"),
            ]
            if clean_search.isdigit():
                search_cond.append(MovieModel.id == int(clean_search))
            stmt = stmt.where(or_(*search_cond))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        stmt = stmt.order_by(MovieModel.id.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        movies = result.scalars().all()

        items = []
        for m in movies:
            flags, issues = evaluate_movie_issues(m)
            items.append(
                AuditItemResponse(
                    id=m.id,
                    content_type="movie",
                    title=m.title,
                    original_title=m.original_title,
                    code=m.code,
                    poster_url=m.poster_url,
                    trailer_url=m.trailer_url,
                    description=m.description,
                    genres=m.genres,
                    release_year=m.release_year,
                    imdb_rating=m.imdb_rating,
                    tmdb_id=m.tmdb_id,
                    source_topic_id=m.source_topic_id,
                    categories=[{"id": c.id, "name": c.name} for c in (m.categories or [])],
                    issues=issues,
                    issues_count=len(issues),
                    **flags,
                )
            )

        return {"items": items, "total": total, "skip": skip, "limit": limit}

    else:
        # Series
        stmt = select(SeriesModel).options(
            selectinload(SeriesModel.categories),
            selectinload(SeriesModel.seasons).selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations),
        )

        issue_cond = get_series_issue_condition(issue_type)
        if issue_cond is not None:
            stmt = stmt.where(issue_cond)

        if clean_search:
            search_cond = [
                SeriesModel.title.ilike(f"%{clean_search}%"),
            ]
            if clean_search.isdigit():
                search_cond.append(SeriesModel.id == int(clean_search))
            stmt = stmt.where(or_(*search_cond))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = await db.scalar(count_stmt) or 0

        stmt = stmt.order_by(SeriesModel.id.desc()).offset(skip).limit(limit)
        result = await db.execute(stmt)
        series_list = result.scalars().all()

        items = []
        for s in series_list:
            flags, issues = evaluate_series_issues(s)
            items.append(
                AuditItemResponse(
                    id=s.id,
                    content_type="series",
                    title=s.title,
                    code=f"S{s.id}",
                    poster_url=s.poster_url,
                    trailer_url=s.trailer_url,
                    description=s.description,
                    genres=None,
                    release_year=s.release_year,
                    imdb_rating=s.imdb_rating,
                    tmdb_id=s.tmdb_id,
                    source_id=s.source_id,
                    categories=[{"id": c.id, "name": c.name} for c in (s.categories or [])],
                    issues=issues,
                    issues_count=len(issues),
                    **flags,
                )
            )

        return {"items": items, "total": total, "skip": skip, "limit": limit}


@router.post("/autofix/{content_type}/{item_id}")
@limiter.limit("20/minute")
async def autofix_item_from_tmdb(
    request: Request,
    content_type: Literal["movie", "series"],
    item_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """
    1-Click Auto-Fix!
    Fetches TMDb data and automatically fills missing poster, uzbek description,
    genres, release year, trailer and ratings.
    """
    if not tmdb_client.api_key:
        raise HTTPException(
            status_code=500,
            detail="TMDb API kaliti serverda sozlanmagan.",
        )

    fixed_fields = []

    if content_type == "movie":
        stmt = select(MovieModel).options(selectinload(MovieModel.categories)).where(MovieModel.id == item_id)
        result = await db.execute(stmt)
        movie = result.scalar_one_or_none()
        if not movie:
            raise HTTPException(status_code=404, detail="Kino topilmadi")

        tmdb_id = movie.tmdb_id
        if not tmdb_id or tmdb_id == 0:
            # Try to search TMDb by title
            results = await tmdb_client.search(query=movie.title, content_type="movie")
            if results and len(results) > 0:
                tmdb_id = results[0]["id"]
                movie.tmdb_id = tmdb_id
                fixed_fields.append("TMDb ID")
            else:
                raise HTTPException(status_code=400, detail="TMDb dan kino topilmadi. Avval TMDb ID ni qo'lda kiriting.")

        details = await tmdb_client.get_details(tmdb_id=tmdb_id, content_type="movie")
        if not details:
            raise HTTPException(status_code=400, detail="TMDb ma'lumotlarini yuklab bo'lmadi")

        # 1. Poster
        if (not movie.poster_url or not movie.poster_url.strip()) and details.get("poster_url"):
            movie.poster_url = details["poster_url"]
            fixed_fields.append("Poster")

        # 2. Description
        if (not movie.description or len(movie.description.strip()) < 30) and details.get("overview"):
            trans_desc, _ = await translator_service.translate_to_uzbek(details["overview"])
            movie.description = trans_desc or details["overview"]
            fixed_fields.append("Tasnif (O'zbekcha)")

        # 3. Genres
        if (not movie.genres or not movie.genres.strip()) and details.get("genres"):
            genres_list = details["genres"]
            movie.genres = ", ".join(genres_list) if isinstance(genres_list, list) else str(genres_list)
            fixed_fields.append("Janrlar")

        # 4. Trailer
        if (not movie.trailer_url or not movie.trailer_url.strip()) and details.get("trailer_url"):
            movie.trailer_url = details["trailer_url"]
            fixed_fields.append("Treyler")

        # 5. Release year
        if (not movie.release_year or movie.release_year == 0) and details.get("release_year"):
            movie.release_year = details["release_year"]
            fixed_fields.append("Chiqqan yili")

        # 6. Ratings
        if (not movie.imdb_rating or movie.imdb_rating == 0) and details.get("vote_average"):
            movie.imdb_rating = round(float(details["vote_average"]), 1)
            movie.tmdb_rating = round(float(details["vote_average"]), 1)
            fixed_fields.append("Reyting")

        # 7. Categories matching
        if (not movie.categories or len(movie.categories) == 0) and details.get("genres"):
            # Map genres to categories
            genre_names = details["genres"] if isinstance(details["genres"], list) else [str(details["genres"])]
            cat_result = await db.execute(select(CategoryModel))
            all_cats = cat_result.scalars().all()
            matched = []
            for c in all_cats:
                for g in genre_names:
                    if g.lower() in c.name.lower() or c.name.lower() in g.lower():
                        matched.append(c)
                        break
            if matched:
                movie.categories = matched
                fixed_fields.append("Kategoriyalar")

        await db.commit()
        await delete_cache_pattern("cache:movies:*")

        return {
            "success": True,
            "message": f"Muvaffaqiyatli to'ldirildi: {', '.join(fixed_fields)}" if fixed_fields else "Barcha maydonlar allaqachon to'liq ekan.",
            "fixed_fields": fixed_fields,
        }

    else:
        # Series
        stmt = select(SeriesModel).options(selectinload(SeriesModel.categories)).where(SeriesModel.id == item_id)
        result = await db.execute(stmt)
        series = result.scalar_one_or_none()
        if not series:
            raise HTTPException(status_code=404, detail="Serial topilmadi")

        tmdb_id = series.tmdb_id
        if not tmdb_id or tmdb_id == 0:
            results = await tmdb_client.search(query=series.title, content_type="tv")
            if results and len(results) > 0:
                tmdb_id = results[0]["id"]
                series.tmdb_id = tmdb_id
                fixed_fields.append("TMDb ID")
            else:
                raise HTTPException(status_code=400, detail="TMDb dan serial topilmadi. Avval TMDb ID ni qo'lda kiriting.")

        details = await tmdb_client.get_details(tmdb_id=tmdb_id, content_type="tv")
        if not details:
            raise HTTPException(status_code=400, detail="TMDb ma'lumotlarini yuklab bo'lmadi")

        # 1. Poster
        if (not series.poster_url or not series.poster_url.strip()) and details.get("poster_url"):
            series.poster_url = details["poster_url"]
            fixed_fields.append("Poster")

        # 2. Description
        if (not series.description or len(series.description.strip()) < 30) and details.get("overview"):
            trans_desc, _ = await translator_service.translate_to_uzbek(details["overview"])
            series.description = trans_desc or details["overview"]
            fixed_fields.append("Tasnif (O'zbekcha)")

        # 3. Trailer
        if (not series.trailer_url or not series.trailer_url.strip()) and details.get("trailer_url"):
            series.trailer_url = details["trailer_url"]
            fixed_fields.append("Treyler")

        # 4. Release year
        if (not series.release_year or series.release_year == 0) and details.get("release_year"):
            series.release_year = details["release_year"]
            fixed_fields.append("Chiqqan yili")

        # 5. Rating
        if (not series.imdb_rating or series.imdb_rating == 0) and details.get("vote_average"):
            series.imdb_rating = round(float(details["vote_average"]), 1)
            fixed_fields.append("Reyting")

        # 6. Categories
        if (not series.categories or len(series.categories) == 0) and details.get("genres"):
            genre_names = details["genres"] if isinstance(details["genres"], list) else [str(details["genres"])]
            cat_result = await db.execute(select(CategoryModel))
            all_cats = cat_result.scalars().all()
            matched = []
            for c in all_cats:
                for g in genre_names:
                    if g.lower() in c.name.lower() or c.name.lower() in g.lower():
                        matched.append(c)
                        break
            if matched:
                series.categories = matched
                fixed_fields.append("Kategoriyalar")

        await db.commit()
        await delete_cache_pattern("cache:series:*")

        return {
            "success": True,
            "message": f"Muvaffaqiyatli to'ldirildi: {', '.join(fixed_fields)}" if fixed_fields else "Barcha maydonlar allaqachon to'liq ekan.",
            "fixed_fields": fixed_fields,
        }


@router.put("/quick-update/{content_type}/{item_id}")
@limiter.limit("30/minute")
async def quick_update_audit_item(
    request: Request,
    content_type: Literal["movie", "series"],
    item_id: int,
    payload: QuickUpdatePayload,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """Update metadata directly from the audit modal without leaving the audit screen."""
    update_data = payload.model_dump(exclude_unset=True)
    category_ids = update_data.pop("category_ids", None)

    if content_type == "movie":
        stmt = select(MovieModel).options(selectinload(MovieModel.categories)).where(MovieModel.id == item_id)
        result = await db.execute(stmt)
        movie = result.scalar_one_or_none()
        if not movie:
            raise HTTPException(status_code=404, detail="Kino topilmadi")

        for key, val in update_data.items():
            setattr(movie, key, val)

        if category_ids is not None:
            cat_stmt = select(CategoryModel).where(CategoryModel.id.in_(category_ids))
            cat_res = await db.execute(cat_stmt)
            movie.categories = list(cat_res.scalars().all())

        await db.commit()
        await delete_cache_pattern("cache:movies:*")
        return {"success": True, "message": "Kino ma'lumotlari muvaffaqiyatli yangilandi"}

    else:
        # Series
        stmt = select(SeriesModel).options(selectinload(SeriesModel.categories)).where(SeriesModel.id == item_id)
        result = await db.execute(stmt)
        series = result.scalar_one_or_none()
        if not series:
            raise HTTPException(status_code=404, detail="Serial topilmadi")

        # Exclude 'genres' since Series doesn't have genres column
        update_data.pop("genres", None)

        for key, val in update_data.items():
            setattr(series, key, val)

        if category_ids is not None:
            cat_stmt = select(CategoryModel).where(CategoryModel.id.in_(category_ids))
            cat_res = await db.execute(cat_stmt)
            series.categories = list(cat_res.scalars().all())

        await db.commit()
        await delete_cache_pattern("cache:series:*")
        return {"success": True, "message": "Serial ma'lumotlari muvaffaqiyatli yangilandi"}
