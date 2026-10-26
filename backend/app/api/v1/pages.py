from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
import re

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

from app.api.deps import get_db_session, get_current_admin
from app.infrastructure.db.models.page import PageModel, page_movie_table, page_series_table
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel
from app.core.cache import get_cache, set_cache, delete_cache_pattern

router = APIRouter(prefix="/pages", tags=["pages"])

# ── Schemas ──────────────────────────────────────────────────────
class PageCreate(BaseModel):
    title: str
    slug: str
    is_active: bool = True

class PageUpdate(BaseModel):
    title: str | None = None
    slug: str | None = None
    is_active: bool | None = None

class PageResponse(BaseModel):
    id: int
    title: str
    slug: str
    is_active: bool
    movies_count: int = 0
    series_count: int = 0

    model_config = {"from_attributes": True}

class PaginatedPagesResponse(BaseModel):
    items: list[PageResponse]
    total: int

class PageContentAction(BaseModel):
    movie_ids: list[int] = []
    series_ids: list[int] = []

class BulkReassignRequest(BaseModel):
    movie_ids: list[int] = []
    series_ids: list[int] = []
    target_page_ids: list[int] = []
    replace: bool = True


# ── Endpoints ────────────────────────────────────────────────────

@router.post("", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
async def create_page(
    page_in: PageCreate,
    session: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Create a new page (Admin only)."""
    clean_slug = slugify(page_in.slug or page_in.title)
    
    # Check duplicate slug
    existing = await session.scalar(select(PageModel).where(PageModel.slug == clean_slug))
    if existing:
        raise HTTPException(status_code=400, detail=f"'{clean_slug}' slugiga ega sahifa allaqachon mavjud")
        
    model = PageModel(
        title=page_in.title.strip(),
        slug=clean_slug,
        is_active=page_in.is_active
    )
    session.add(model)
    await session.commit()
    await session.refresh(model)
    await delete_cache_pattern("cache:pages:*")
    
    return PageResponse(
        id=model.id,
        title=model.title,
        slug=model.slug,
        is_active=model.is_active,
        movies_count=0,
        series_count=0
    )


@router.get("", response_model=PaginatedPagesResponse)
async def list_pages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    search: str | None = Query(None),
    is_active: bool | None = Query(None),
    session: AsyncSession = Depends(get_db_session)
):
    """List all pages with movies_count and series_count (Public / Admin)."""
    # Subqueries for counts
    movie_cnt = (
        select(func.count(page_movie_table.c.movie_id))
        .where(page_movie_table.c.page_id == PageModel.id)
        .correlate(PageModel)
        .scalar_subquery()
    )
    series_cnt = (
        select(func.count(page_series_table.c.series_id))
        .where(page_series_table.c.page_id == PageModel.id)
        .correlate(PageModel)
        .scalar_subquery()
    )

    query = select(PageModel, movie_cnt.label("movies_count"), series_cnt.label("series_count"))
    count_query = select(func.count()).select_from(PageModel)

    if search:
        search_filter = or_(
            PageModel.title.ilike(f"%{search.strip()}%"),
            PageModel.slug.ilike(f"%{search.strip()}%")
        )
        query = query.where(search_filter)
        count_query = count_query.where(search_filter)

    if is_active is not None:
        query = query.where(PageModel.is_active == is_active)
        count_query = count_query.where(PageModel.is_active == is_active)

    total = await session.scalar(count_query) or 0
    query = query.order_by(PageModel.id.asc()).offset(skip).limit(limit)
    result = await session.execute(query)

    items = []
    for row in result.all():
        p_model, m_c, s_c = row
        items.append(
            PageResponse(
                id=p_model.id,
                title=p_model.title,
                slug=p_model.slug,
                is_active=p_model.is_active,
                movies_count=m_c or 0,
                series_count=s_c or 0
            )
        )

    return {"items": items, "total": total}


@router.get("/{page_id_or_slug}/content")
async def get_page_content(
    page_id_or_slug: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get all movies and series attached to a specific page."""
    if page_id_or_slug.isdigit():
        page_stmt = select(PageModel).where(PageModel.id == int(page_id_or_slug))
    else:
        page_stmt = select(PageModel).where(PageModel.slug == page_id_or_slug)

    res = await session.execute(page_stmt)
    page = res.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Sahifa topilmadi")

    # Fetch attached movies
    movie_stmt = (
        select(MovieModel)
        .join(page_movie_table, page_movie_table.c.movie_id == MovieModel.id)
        .where(page_movie_table.c.page_id == page.id)
        .order_by(MovieModel.id.desc())
    )
    movies_res = await session.execute(movie_stmt)
    movies = movies_res.scalars().all()

    # Fetch attached series
    series_stmt = (
        select(SeriesModel)
        .join(page_series_table, page_series_table.c.series_id == SeriesModel.id)
        .where(page_series_table.c.page_id == page.id)
        .order_by(SeriesModel.id.desc())
    )
    series_res = await session.execute(series_stmt)
    series_list = series_res.scalars().all()

    return {
        "page": {
            "id": page.id,
            "title": page.title,
            "slug": page.slug,
            "is_active": page.is_active,
            "movies_count": len(movies),
            "series_count": len(series_list),
        },
        "movies": [
            {
                "id": m.id,
                "title": m.title,
                "code": getattr(m, "code", None),
                "year": getattr(m, "year", None),
                "poster_url": getattr(m, "poster_url", None),
                "genres": getattr(m, "genres", None),
                "publish_status": getattr(m, "publish_status", None),
            }
            for m in movies
        ],
        "series": [
            {
                "id": s.id,
                "title": s.title,
                "code": getattr(s, "code", None),
                "year": getattr(s, "year", None),
                "poster_url": getattr(s, "poster_url", None),
                "genres": getattr(s, "genres", None),
                "publish_status": getattr(s, "publish_status", None),
            }
            for s in series_list
        ],
    }


@router.post("/{page_id}/attach")
async def attach_content_to_page(
    page_id: int,
    payload: PageContentAction,
    session: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Attach movies or series to a page (Admin only)."""
    result = await session.execute(select(PageModel).where(PageModel.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Sahifa topilmadi")

    if payload.movie_ids:
        from sqlalchemy.orm import selectinload
        stmt = select(MovieModel).options(selectinload(MovieModel.pages)).where(MovieModel.id.in_(payload.movie_ids))
        res = await session.execute(stmt)
        for m in res.scalars().all():
            if page.id not in {p.id for p in m.pages}:
                m.pages.append(page)

    if payload.series_ids:
        from sqlalchemy.orm import selectinload
        stmt = select(SeriesModel).options(selectinload(SeriesModel.pages)).where(SeriesModel.id.in_(payload.series_ids))
        res = await session.execute(stmt)
        for s in res.scalars().all():
            if page.id not in {p.id for p in s.pages}:
                s.pages.append(page)

    await session.commit()
    await delete_cache_pattern("cache:pages:*")
    await delete_cache_pattern("cache:movies:*")
    await delete_cache_pattern("cache:series:*")
    return {"success": True, "page_id": page.id, "attached_movies": len(payload.movie_ids), "attached_series": len(payload.series_ids)}


@router.post("/{page_id}/detach")
async def detach_content_from_page(
    page_id: int,
    payload: PageContentAction,
    session: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Detach movies or series from a page (Admin only)."""
    result = await session.execute(select(PageModel).where(PageModel.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Sahifa topilmadi")

    if payload.movie_ids:
        from sqlalchemy.orm import selectinload
        stmt = select(MovieModel).options(selectinload(MovieModel.pages)).where(MovieModel.id.in_(payload.movie_ids))
        res = await session.execute(stmt)
        for m in res.scalars().all():
            m.pages = [p for p in m.pages if p.id != page.id]

    if payload.series_ids:
        from sqlalchemy.orm import selectinload
        stmt = select(SeriesModel).options(selectinload(SeriesModel.pages)).where(SeriesModel.id.in_(payload.series_ids))
        res = await session.execute(stmt)
        for s in res.scalars().all():
            s.pages = [p for p in s.pages if p.id != page.id]

    await session.commit()
    await delete_cache_pattern("cache:pages:*")
    await delete_cache_pattern("cache:movies:*")
    await delete_cache_pattern("cache:series:*")
    return {"success": True, "page_id": page.id, "detached_movies": len(payload.movie_ids), "detached_series": len(payload.series_ids)}


@router.get("/{slug}", response_model=PageResponse)
async def get_page(
    slug: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get page by slug (Public)."""
    movie_cnt = (
        select(func.count(page_movie_table.c.movie_id))
        .where(page_movie_table.c.page_id == PageModel.id)
        .correlate(PageModel)
        .scalar_subquery()
    )
    series_cnt = (
        select(func.count(page_series_table.c.series_id))
        .where(page_series_table.c.page_id == PageModel.id)
        .correlate(PageModel)
        .scalar_subquery()
    )

    if slug.isdigit():
        stmt = select(PageModel, movie_cnt.label("movies_count"), series_cnt.label("series_count")).where(PageModel.id == int(slug))
    else:
        stmt = select(PageModel, movie_cnt.label("movies_count"), series_cnt.label("series_count")).where(PageModel.slug == slug)

    result = await session.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Page not found")
        
    p_model, m_c, s_c = row
    return PageResponse(
        id=p_model.id,
        title=p_model.title,
        slug=p_model.slug,
        is_active=p_model.is_active,
        movies_count=m_c or 0,
        series_count=s_c or 0
    )


@router.put("/{page_id}", response_model=PageResponse)
async def update_page(
    page_id: int,
    page_in: PageUpdate,
    session: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Update a page (Admin only)."""
    result = await session.execute(select(PageModel).where(PageModel.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
        
    update_data = page_in.model_dump(exclude_unset=True)
    if "slug" in update_data and update_data["slug"]:
        update_data["slug"] = slugify(update_data["slug"])
        
    for key, value in update_data.items():
        setattr(page, key, value)
        
    await session.commit()
    await session.refresh(page)
    await delete_cache_pattern("cache:pages:*")
    
    # Get current counts
    m_count = await session.scalar(
        select(func.count(page_movie_table.c.movie_id)).where(page_movie_table.c.page_id == page.id)
    ) or 0
    s_count = await session.scalar(
        select(func.count(page_series_table.c.series_id)).where(page_series_table.c.page_id == page.id)
    ) or 0

    return PageResponse(
        id=page.id,
        title=page.title,
        slug=page.slug,
        is_active=page.is_active,
        movies_count=m_count,
        series_count=s_count
    )


@router.delete("/{page_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_page(
    page_id: int,
    session: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Delete a page (Admin only)."""
    result = await session.execute(select(PageModel).where(PageModel.id == page_id))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
        
    await session.delete(page)
    await session.commit()
    await delete_cache_pattern("cache:pages:*")


@router.post("/bulk-reassign")
async def bulk_reassign_pages(
    payload: BulkReassignRequest,
    session: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Search & Mark bulk reassignment of movies/series to specific page(s)."""
    target_pages = []
    if payload.target_page_ids:
        res = await session.execute(select(PageModel).where(PageModel.id.in_(payload.target_page_ids)))
        target_pages = list(res.scalars().all())

    # Update Movies
    if payload.movie_ids:
        from sqlalchemy.orm import selectinload
        stmt = select(MovieModel).options(selectinload(MovieModel.pages)).where(MovieModel.id.in_(payload.movie_ids))
        res = await session.execute(stmt)
        movies = res.scalars().all()
        for m in movies:
            if payload.replace:
                m.pages = list(target_pages)
            else:
                existing_ids = {p.id for p in m.pages}
                for tp in target_pages:
                    if tp.id not in existing_ids:
                        m.pages.append(tp)

    # Update Series
    if payload.series_ids:
        from sqlalchemy.orm import selectinload
        stmt = select(SeriesModel).options(selectinload(SeriesModel.pages)).where(SeriesModel.id.in_(payload.series_ids))
        res = await session.execute(stmt)
        series_list = res.scalars().all()
        for s in series_list:
            if payload.replace:
                s.pages = list(target_pages)
            else:
                existing_ids = {p.id for p in s.pages}
                for tp in target_pages:
                    if tp.id not in existing_ids:
                        s.pages.append(tp)

    await session.commit()
    await delete_cache_pattern("cache:pages:*")
    await delete_cache_pattern("cache:movies:*")
    await delete_cache_pattern("cache:series:*")

    return {
        "success": True,
        "movies_updated": len(payload.movie_ids),
        "series_updated": len(payload.series_ids),
        "target_pages": [p.title for p in target_pages]
    }
