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
from app.infrastructure.db.models.watch_history import WatchHistoryModel
from app.infrastructure.db.models.review import ReviewModel
from app.infrastructure.db.models.collection import CollectionItemModel
from app.infrastructure.db.models.series_subscription import SeriesSubscriptionModel
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
            missing_genres=0,
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


# ── Advanced Audit & Quality Control Endpoints ───────────────────

class MergeDuplicatesRequest(BaseModel):
    content_type: Literal["movie", "series"]
    primary_id: int
    duplicate_id: int
    keep_better_video: bool = True


@router.get("/duplicates")
@limiter.limit("30/minute")
async def find_duplicates(
    request: Request,
    content_type: Literal["movie", "series"] = "movie",
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """
    Smart Duplicate Finder:
    Matches duplicates based on:
    1. Identical TMDb ID (> 0)
    2. Normalized title similarity
    """
    duplicates_groups = []

    if content_type == "movie":
        # 1. TMDb ID based
        tmdb_dup_query = (
            select(MovieModel.tmdb_id)
            .where(MovieModel.tmdb_id.isnot(None), MovieModel.tmdb_id > 0)
            .group_by(MovieModel.tmdb_id)
            .having(func.count(MovieModel.id) > 1)
        )
        tmdb_dups = (await db.execute(tmdb_dup_query)).scalars().all()

        for tid in tmdb_dups:
            stmt = (
                select(MovieModel)
                .options(selectinload(MovieModel.translations))
                .where(MovieModel.tmdb_id == tid)
                .order_by(MovieModel.id.asc())
            )
            movies = (await db.execute(stmt)).scalars().all()
            duplicates_groups.append({
                "match_reason": f"TMDb ID: {tid}",
                "items": [
                    {
                        "id": m.id,
                        "title": m.title,
                        "original_title": m.original_title,
                        "code": m.code,
                        "release_year": m.release_year,
                        "poster_url": m.poster_url,
                        "translations_count": len(m.translations or []),
                        "has_video": any(bool(t.telegram_file_id) for t in (m.translations or [])),
                        "source_topic_id": m.source_topic_id,
                        "created_at": m.created_at.isoformat() if m.created_at else None,
                    }
                    for m in movies
                ]
            })

        # 2. Normalized title matching (using Uzbek stem normalization)
        all_movies_stmt = select(MovieModel.id, MovieModel.title, MovieModel.original_title, MovieModel.release_year, MovieModel.code, MovieModel.poster_url).order_by(MovieModel.id.desc()).limit(1500)
        all_m = (await db.execute(all_movies_stmt)).all()
        import re

        def uzbek_stem_word(word: str) -> str:
            if not word or len(word) < 4:
                return word
            w = word.lower()
            w = re.sub(r'(?:larning|larimiz|laringiz|larida|laridan|lariga|larini)$', '', w)
            if len(w) >= 5:
                w = re.sub(r'(?:dagi|ning|dan|lar|ga|ka|qa|da|ni|si|imiz|ingiz)$', '', w)
            if len(w) >= 4 and w.endswith('i') and w[-2] not in 'aeiouy':
                w = w[:-1]
            return w if len(w) >= 3 else word

        def norm_stem(t: str) -> str:
            if not t:
                return ""
            cleaned = re.sub(r"[^\w\s]", "", t.lower()).strip()
            words = [uzbek_stem_word(w) for w in cleaned.split() if w]
            return "".join(words)

        already_grouped_ids = {m["id"] for g in duplicates_groups for m in g["items"]}
        seen_titles = {}
        for mid, mtitle, morig, myear, mcode, mposter in all_m:
            clean = norm_stem(mtitle)
            if not clean or len(clean) < 3:
                continue
            key = f"{clean}_{myear}" if myear else clean
            item_entry = {"id": mid, "title": mtitle, "year": myear, "code": mcode, "poster_url": mposter}
            if key in seen_titles:
                seen_titles[key].append(item_entry)
            else:
                seen_titles[key] = [item_entry]

        for k, items in seen_titles.items():
            if len(items) > 1 and not any(cand["id"] in already_grouped_ids for cand in items):
                duplicates_groups.append({
                    "match_reason": f"Nom o'xshashligi: {items[0]['title']}",
                    "items": items
                })
                already_grouped_ids.update(cand["id"] for cand in items)

    else:
        # Series
        import re

        def uzbek_stem_word(word: str) -> str:
            if not word or len(word) < 4:
                return word
            w = word.lower()
            w = re.sub(r'(?:larning|larimiz|laringiz|larida|laridan|lariga|larini)$', '', w)
            if len(w) >= 5:
                w = re.sub(r'(?:dagi|ning|dan|lar|ga|ka|qa|da|ni|si|imiz|ingiz)$', '', w)
            if len(w) >= 4 and w.endswith('i') and w[-2] not in 'aeiouy':
                w = w[:-1]
            return w if len(w) >= 3 else word

        def norm_stem(t: str) -> str:
            if not t:
                return ""
            cleaned = re.sub(r"[^\w\s]", "", t.lower()).strip()
            words = [uzbek_stem_word(w) for w in cleaned.split() if w]
            return "".join(words)

        # 1. TMDb ID based duplicate series
        tmdb_dup_query = (
            select(SeriesModel.tmdb_id)
            .where(SeriesModel.tmdb_id.isnot(None), SeriesModel.tmdb_id > 0)
            .group_by(SeriesModel.tmdb_id)
            .having(func.count(SeriesModel.id) > 1)
        )
        tmdb_dups = (await db.execute(tmdb_dup_query)).scalars().all()

        for tid in tmdb_dups:
            stmt = (
                select(
                    SeriesModel.id,
                    SeriesModel.title,
                    SeriesModel.release_year,
                    SeriesModel.poster_url,
                    SeriesModel.created_at,
                    func.count(func.distinct(SeasonModel.id)).label("seasons_count"),
                    func.count(func.distinct(EpisodeModel.id)).label("episodes_count"),
                )
                .outerjoin(SeasonModel, SeasonModel.series_id == SeriesModel.id)
                .outerjoin(EpisodeModel, EpisodeModel.season_id == SeasonModel.id)
                .where(SeriesModel.tmdb_id == tid)
                .group_by(SeriesModel.id)
                .order_by(SeriesModel.id.asc())
            )
            series_list = (await db.execute(stmt)).all()
            duplicates_groups.append({
                "match_reason": f"TMDb ID: {tid}",
                "items": [
                    {
                        "id": s.id,
                        "title": s.title,
                        "code": f"S{s.id}",
                        "release_year": s.release_year,
                        "poster_url": s.poster_url,
                        "seasons_count": s.seasons_count or 0,
                        "episodes_count": s.episodes_count or 0,
                        "created_at": s.created_at.isoformat() if s.created_at else None,
                    }
                    for s in series_list
                ]
            })

        # 2. Stemmed title similarity for Series (finds e.g. Iyerusalimning vs Iyerusalim)
        already_grouped_series_ids = {m["id"] for g in duplicates_groups for m in g["items"]}
        all_series_stmt = (
            select(
                SeriesModel.id,
                SeriesModel.title,
                SeriesModel.release_year,
                SeriesModel.poster_url,
                SeriesModel.created_at,
                func.count(func.distinct(SeasonModel.id)).label("seasons_count"),
                func.count(func.distinct(EpisodeModel.id)).label("episodes_count"),
            )
            .outerjoin(SeasonModel, SeasonModel.series_id == SeriesModel.id)
            .outerjoin(EpisodeModel, EpisodeModel.season_id == SeasonModel.id)
            .group_by(SeriesModel.id)
            .order_by(SeriesModel.id.desc())
            .limit(1500)
        )
        all_s = (await db.execute(all_series_stmt)).all()

        seen_series = {}
        for s in all_s:
            clean = norm_stem(s.title)
            if not clean or len(clean) < 3:
                continue
            key = f"{clean}_{s.release_year}" if s.release_year else clean
            item_entry = {
                "id": s.id,
                "title": s.title,
                "code": f"S{s.id}",
                "release_year": s.release_year,
                "poster_url": s.poster_url,
                "seasons_count": s.seasons_count or 0,
                "episodes_count": s.episodes_count or 0,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            if key in seen_series:
                seen_series[key].append(item_entry)
            else:
                seen_series[key] = [item_entry]

        for k, items in seen_series.items():
            if len(items) > 1 and not any(cand["id"] in already_grouped_series_ids for cand in items):
                duplicates_groups.append({
                    "match_reason": f"Nom o'xshashligi: {items[0]['title']}",
                    "items": items
                })
                already_grouped_series_ids.update(cand["id"] for cand in items)

    return {"total_groups": len(duplicates_groups), "groups": duplicates_groups}


@router.post("/merge-duplicates")
@limiter.limit("20/minute")
async def merge_duplicates(
    request: Request,
    payload: MergeDuplicatesRequest,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """
    Smart Merge:
    Merges duplicate into primary.
    Preserves highest quality video / translations and cleans up duplicate.
    Also deletes Telegram topic of duplicate if present.
    """
    if payload.primary_id == payload.duplicate_id:
        raise HTTPException(status_code=400, detail="Asosiy va dublikat ID lari bir xil bo'lishi mumkin emas.")

    if payload.content_type == "movie":
        stmt_p = select(MovieModel).options(selectinload(MovieModel.translations), selectinload(MovieModel.categories), selectinload(MovieModel.pages)).where(MovieModel.id == payload.primary_id)
        primary = (await db.execute(stmt_p)).scalar_one_or_none()
        stmt_d = select(MovieModel).options(selectinload(MovieModel.translations), selectinload(MovieModel.categories), selectinload(MovieModel.pages)).where(MovieModel.id == payload.duplicate_id)
        dup = (await db.execute(stmt_d)).scalar_one_or_none()

        if not primary or not dup:
            raise HTTPException(status_code=404, detail="Asosiy yoki dublikat kino topilmadi.")

        # Copy missing translations from dup to primary
        existing_langs = {t.language for t in (primary.translations or [])}
        for dt in (dup.translations or []):
            if dt.language not in existing_langs and dt.telegram_file_id:
                new_tr = MovieTranslationModel(
                    movie_id=primary.id,
                    language=dt.language,
                    telegram_file_id=dt.telegram_file_id,
                    storage_channel_message_id=dt.storage_channel_message_id,
                )
                db.add(new_tr)

        # Fill missing metadata on primary
        if (not primary.poster_url or not primary.poster_url.strip()) and dup.poster_url:
            primary.poster_url = dup.poster_url
        if (not primary.description or len(primary.description.strip()) < 30) and dup.description:
            primary.description = dup.description
        if not primary.genres and dup.genres:
            primary.genres = dup.genres
        if not primary.trailer_url and dup.trailer_url:
            primary.trailer_url = dup.trailer_url

        # Copy missing categories & pages
        prim_cat_ids = {c.id for c in primary.categories}
        for c in dup.categories:
            if c.id not in prim_cat_ids:
                primary.categories.append(c)

        prim_page_ids = {p.id for p in primary.pages}
        for p in dup.pages:
            if p.id not in prim_page_ids:
                primary.pages.append(p)

        # Migrate associated WatchHistoryModel
        stmt_wh = select(WatchHistoryModel).where(WatchHistoryModel.movie_id == dup.id)
        dup_wh_list = (await db.execute(stmt_wh)).scalars().all()
        if dup_wh_list:
            stmt_p_wh = select(WatchHistoryModel.user_id).where(WatchHistoryModel.movie_id == primary.id)
            prim_wh_user_ids = set((await db.execute(stmt_p_wh)).scalars().all())
            for wh in dup_wh_list:
                if wh.user_id not in prim_wh_user_ids:
                    wh.movie_id = primary.id
                    prim_wh_user_ids.add(wh.user_id)
                else:
                    await db.delete(wh)

        # Migrate associated ReviewModel
        stmt_rev = select(ReviewModel).where(ReviewModel.movie_id == dup.id)
        dup_rev_list = (await db.execute(stmt_rev)).scalars().all()
        if dup_rev_list:
            stmt_p_rev = select(ReviewModel.user_id).where(ReviewModel.movie_id == primary.id)
            prim_rev_user_ids = set((await db.execute(stmt_p_rev)).scalars().all())
            for rev in dup_rev_list:
                if rev.user_id not in prim_rev_user_ids:
                    rev.movie_id = primary.id
                    prim_rev_user_ids.add(rev.user_id)
                else:
                    await db.delete(rev)

        # Migrate associated CollectionItemModel
        stmt_ci = select(CollectionItemModel).where(CollectionItemModel.movie_id == dup.id)
        dup_ci_list = (await db.execute(stmt_ci)).scalars().all()
        if dup_ci_list:
            stmt_p_ci = select(CollectionItemModel.collection_id).where(CollectionItemModel.movie_id == primary.id)
            prim_ci_collection_ids = set((await db.execute(stmt_p_ci)).scalars().all())
            for ci in dup_ci_list:
                if ci.collection_id not in prim_ci_collection_ids:
                    ci.movie_id = primary.id
                    prim_ci_collection_ids.add(ci.collection_id)
                else:
                    await db.delete(ci)

        # Delete duplicate topic in Telegram if exists
        if dup.source_chat_id and dup.source_topic_id:
            try:
                from app.infrastructure.telegram.telegram_client import telegram_client
                await telegram_client.delete_forum_topic(dup.source_chat_id, dup.source_topic_id)
            except Exception as e:
                logger.warning(f"Failed to delete duplicate movie topic: {e}")

        # Delete duplicate from DB
        await db.delete(dup)
        await db.commit()
        await delete_cache_pattern("cache:movies:*")

        return {"success": True, "message": f"Kino muvaffaqiyatli birlashtirildi (ID: {primary.id}) va dublikat o'chirildi."}

    else:
        # Series merge
        stmt_p = select(SeriesModel).options(selectinload(SeriesModel.seasons).selectinload(SeasonModel.episodes), selectinload(SeriesModel.categories), selectinload(SeriesModel.pages)).where(SeriesModel.id == payload.primary_id)
        primary = (await db.execute(stmt_p)).scalar_one_or_none()
        stmt_d = select(SeriesModel).options(selectinload(SeriesModel.seasons).selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations), selectinload(SeriesModel.categories), selectinload(SeriesModel.pages), selectinload(SeriesModel.source)).where(SeriesModel.id == payload.duplicate_id)
        dup = (await db.execute(stmt_d)).scalar_one_or_none()

        if not primary or not dup:
            raise HTTPException(status_code=404, detail="Asosiy yoki dublikat serial topilmadi.")

        # Re-link missing seasons/episodes
        prim_season_map = {s.season_number: s for s in (primary.seasons or [])}
        for d_sz in (dup.seasons or []):
            if d_sz.season_number not in prim_season_map:
                d_sz.series_id = primary.id
            else:
                target_sz = prim_season_map[d_sz.season_number]
                target_ep_nums = {ep.episode_number for ep in (target_sz.episodes or [])}
                for ep in (d_sz.episodes or []):
                    if ep.episode_number not in target_ep_nums:
                        ep.season_id = target_sz.id

        # Fill missing metadata on primary series
        if (not primary.poster_url or not primary.poster_url.strip()) and dup.poster_url:
            primary.poster_url = dup.poster_url
        if (not primary.description or len(primary.description.strip()) < 30) and dup.description:
            primary.description = dup.description
        if not primary.trailer_url and dup.trailer_url:
            primary.trailer_url = dup.trailer_url

        # Copy missing categories & pages
        prim_cat_ids = {c.id for c in primary.categories}
        for c in dup.categories:
            if c.id not in prim_cat_ids:
                primary.categories.append(c)

        prim_page_ids = {p.id for p in primary.pages}
        for p in dup.pages:
            if p.id not in prim_page_ids:
                primary.pages.append(p)

        # Migrate associated ReviewModel
        stmt_rev = select(ReviewModel).where(ReviewModel.series_id == dup.id)
        dup_rev_list = (await db.execute(stmt_rev)).scalars().all()
        if dup_rev_list:
            stmt_p_rev = select(ReviewModel.user_id).where(ReviewModel.series_id == primary.id)
            prim_rev_user_ids = set((await db.execute(stmt_p_rev)).scalars().all())
            for rev in dup_rev_list:
                if rev.user_id not in prim_rev_user_ids:
                    rev.series_id = primary.id
                    prim_rev_user_ids.add(rev.user_id)
                else:
                    await db.delete(rev)

        # Migrate associated CollectionItemModel
        stmt_ci = select(CollectionItemModel).where(CollectionItemModel.series_id == dup.id)
        dup_ci_list = (await db.execute(stmt_ci)).scalars().all()
        if dup_ci_list:
            stmt_p_ci = select(CollectionItemModel.collection_id).where(CollectionItemModel.series_id == primary.id)
            prim_ci_collection_ids = set((await db.execute(stmt_p_ci)).scalars().all())
            for ci in dup_ci_list:
                if ci.collection_id not in prim_ci_collection_ids:
                    ci.series_id = primary.id
                    prim_ci_collection_ids.add(ci.collection_id)
                else:
                    await db.delete(ci)

        # Migrate associated SeriesSubscriptionModel
        stmt_sub = select(SeriesSubscriptionModel).where(SeriesSubscriptionModel.series_id == dup.id)
        dup_sub_list = (await db.execute(stmt_sub)).scalars().all()
        if dup_sub_list:
            stmt_p_sub = select(SeriesSubscriptionModel.telegram_user_id).where(SeriesSubscriptionModel.series_id == primary.id)
            prim_sub_user_ids = set((await db.execute(stmt_p_sub)).scalars().all())
            for sub in dup_sub_list:
                if sub.telegram_user_id not in prim_sub_user_ids:
                    sub.series_id = primary.id
                    prim_sub_user_ids.add(sub.telegram_user_id)
                else:
                    await db.delete(sub)

        # Delete duplicate series topic in Telegram if exists
        if dup.source and dup.source.chat_id and dup.source.topic_id:
            try:
                from app.infrastructure.telegram.telegram_client import telegram_client
                await telegram_client.delete_forum_topic(dup.source.chat_id, dup.source.topic_id)
            except Exception as e:
                logger.warning(f"Failed to delete duplicate series topic: {e}")

        # Delete duplicate series from DB
        await db.delete(dup)
        await db.commit()
        await delete_cache_pattern("cache:series:*")

        return {"success": True, "message": f"Serial muvaffaqiyatli birlashtirildi (ID: {primary.id}) va dublikat o'chirildi."}


@router.get("/sequence-gaps")
@limiter.limit("30/minute")
async def check_sequence_gaps(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """
    Checks all series seasons for missing episode numbers in the sequence (e.g. 1 to 41 gap).
    High-performance SQL query: selects only seasons where MAX(episode_number) > COUNT(episodes).
    """
    gap_seasons_stmt = (
        select(
            SeriesModel.id.label("series_id"),
            SeriesModel.title.label("series_title"),
            SeasonModel.id.label("season_id"),
            SeasonModel.season_number.label("season_number"),
            func.count(EpisodeModel.id).label("total_episodes"),
            func.max(EpisodeModel.episode_number).label("max_episode_number"),
        )
        .join(SeasonModel, SeasonModel.series_id == SeriesModel.id)
        .join(EpisodeModel, EpisodeModel.season_id == SeasonModel.id)
        .group_by(SeriesModel.id, SeriesModel.title, SeasonModel.id, SeasonModel.season_number)
        .having(
            func.count(EpisodeModel.id) >= 2,
            func.max(EpisodeModel.episode_number) > func.count(EpisodeModel.id)
        )
        .order_by(SeriesModel.id.desc())
        .limit(200)
    )
    gap_seasons = (await db.execute(gap_seasons_stmt)).all()

    if not gap_seasons:
        return {"total_gaps": 0, "items": []}

    season_ids = [row.season_id for row in gap_seasons]
    ep_stmt = (
        select(EpisodeModel.season_id, EpisodeModel.episode_number)
        .where(EpisodeModel.season_id.in_(season_ids))
        .order_by(EpisodeModel.season_id, EpisodeModel.episode_number)
    )
    ep_rows = (await db.execute(ep_stmt)).all()

    season_ep_map = {}
    for s_id, ep_num in ep_rows:
        if s_id not in season_ep_map:
            season_ep_map[s_id] = set()
        season_ep_map[s_id].add(ep_num)

    gaps = []
    for row in gap_seasons:
        ep_numbers = season_ep_map.get(row.season_id, set())
        max_num = row.max_episode_number or 0
        if max_num > len(ep_numbers):
            missing = sorted(list(set(range(1, max_num + 1)) - ep_numbers))
            if missing:
                gaps.append({
                    "series_id": row.series_id,
                    "series_title": row.series_title,
                    "season_id": row.season_id,
                    "season_number": row.season_number,
                    "total_episodes": row.total_episodes,
                    "max_episode_number": max_num,
                    "missing_count": len(missing),
                    "missing_episodes": missing[:20],
                    "gap_summary": f"1 dan {max_num} gacha bo'lgan ketma-ketlikda {len(missing)} ta qism yetishmayapti",
                })

    return {"total_gaps": len(gaps), "items": gaps}


@router.get("/incomplete-series")
@limiter.limit("30/minute")
async def check_incomplete_series(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """
    Finds series where season.episode_count is known but actual episodes in DB is fewer.
    Sorted by biggest gap descending.
    Fast grouped SQL query executed directly on DB.
    """
    stmt = (
        select(
            SeriesModel.id.label("series_id"),
            SeriesModel.title.label("series_title"),
            SeriesModel.poster_url.label("poster_url"),
            SeasonModel.season_number.label("season_number"),
            SeasonModel.episode_count.label("expected_episodes"),
            func.count(EpisodeModel.id).label("existing_episodes"),
            (SeasonModel.episode_count - func.count(EpisodeModel.id)).label("missing_count"),
        )
        .join(SeasonModel, SeasonModel.series_id == SeriesModel.id)
        .outerjoin(EpisodeModel, EpisodeModel.season_id == SeasonModel.id)
        .where(SeasonModel.episode_count.isnot(None), SeasonModel.episode_count > 0)
        .group_by(SeriesModel.id, SeriesModel.title, SeriesModel.poster_url, SeasonModel.id, SeasonModel.season_number, SeasonModel.episode_count)
        .having(func.count(EpisodeModel.id) < SeasonModel.episode_count)
        .order_by((SeasonModel.episode_count - func.count(EpisodeModel.id)).desc())
        .limit(200)
    )
    rows = (await db.execute(stmt)).all()

    incomplete = [
        {
            "series_id": r.series_id,
            "series_title": r.series_title,
            "season_number": r.season_number,
            "expected_episodes": r.expected_episodes,
            "existing_episodes": r.existing_episodes,
            "missing_count": r.missing_count,
            "poster_url": r.poster_url,
        }
        for r in rows
    ]

    return {"total_incomplete": len(incomplete), "items": incomplete}


@router.get("/orphan-episodes")
@limiter.limit("30/minute")
async def check_orphan_episodes(
    request: Request,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """
    Finds episodes that don't belong to any valid season or whose season doesn't belong to any series.
    """
    # Episodes whose season_id doesn't exist in seasons table
    stmt = (
        select(EpisodeModel)
        .outerjoin(SeasonModel, EpisodeModel.season_id == SeasonModel.id)
        .where(SeasonModel.id.is_(None))
    )
    orphans = (await db.execute(stmt)).scalars().all()

    return {
        "total_orphans": len(orphans),
        "items": [
            {
                "id": ep.id,
                "code": ep.code,
                "display_code": ep.display_code,
                "season_id": ep.season_id,
                "created_at": ep.created_at.isoformat() if ep.created_at else None,
            }
            for ep in orphans
        ]
    }


@router.delete("/cascade-delete/{content_type}/{item_id}", status_code=status.HTTP_200_OK)
async def cascade_delete_item(
    content_type: str,
    item_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """
    1-Click Full Cascade Deletion:
    Deletes Telegram Forum Topic + DB entries + Caches.
    """
    from app.infrastructure.telegram.telegram_client import telegram_client

    topic_deleted = False
    c_type = (content_type or "").lower().strip()

    if c_type in ("movie", "movies"):
        movie = await db.get(MovieModel, item_id)
        if not movie:
            return {
                "success": True,
                "message": "Kino allaqachon bazadan o'chirilgan.",
                "telegram_topic_deleted": False
            }

        if movie.source_chat_id and movie.source_topic_id:
            try:
                topic_deleted = await telegram_client.delete_forum_topic(movie.source_chat_id, movie.source_topic_id)
            except Exception as e:
                logger.warning(f"Cascade topic delete failed: {e}")

        await db.delete(movie)
        await db.commit()
        await delete_cache_pattern("cache:movies:*")
        return {
            "success": True,
            "message": "Kino va unga bog'liq barcha ma'lumotlar to'liq kaskad tarzda o'chirildi.",
            "telegram_topic_deleted": topic_deleted
        }

    elif c_type in ("series", "tv", "show"):
        stmt = select(SeriesModel).options(selectinload(SeriesModel.source)).where(SeriesModel.id == item_id)
        res = await db.execute(stmt)
        series = res.scalar_one_or_none()
        if not series:
            return {
                "success": True,
                "message": "Serial allaqachon bazadan o'chirilgan.",
                "telegram_topic_deleted": False
            }

        if series.source and series.source.chat_id and series.source.topic_id:
            try:
                topic_deleted = await telegram_client.delete_forum_topic(series.source.chat_id, series.source.topic_id)
            except Exception as e:
                logger.warning(f"Cascade topic delete failed: {e}")

        await db.delete(series)
        await db.commit()
        await delete_cache_pattern("cache:series:*")
        return {
            "success": True,
            "message": "Serial va uning barcha fasllari, qismlari kaskad tarzda o'chirildi.",
            "telegram_topic_deleted": topic_deleted
        }

    else:
        raise HTTPException(status_code=400, detail=f"Noto'g'ri content_type: '{content_type}'. Faqat 'movie' yoki 'series' qabul qilinadi.")


