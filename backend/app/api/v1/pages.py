from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import re

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')

from app.api.deps import get_db_session, get_current_admin
from app.infrastructure.db.models.page import PageModel
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

    model_config = {"from_attributes": True}

class PaginatedPagesResponse(BaseModel):
    items: list[PageResponse]
    total: int


# ── Endpoints ────────────────────────────────────────────────────
@router.post("", response_model=PageResponse, status_code=status.HTTP_201_CREATED)
async def create_page(
    page_in: PageCreate,
    session: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Create a new page (Admin only)."""
    data = page_in.model_dump()
    data["slug"] = slugify(data["slug"])
    model = PageModel(**data)
    session.add(model)
    await session.commit()
    await session.refresh(model)
    await delete_cache_pattern("cache:pages:*")
    return model

@router.get("", response_model=PaginatedPagesResponse)
async def list_pages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    session: AsyncSession = Depends(get_db_session)
):
    """List all pages (Public)."""
    cache_key = f"cache:pages:list:{skip}:{limit}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    from sqlalchemy import func
    
    count_query = select(func.count()).select_from(PageModel)
    total = await session.scalar(count_query)
    
    query = select(PageModel).offset(skip).limit(limit)
    result = await session.execute(query)
    items = result.scalars().all()
    
    response_data = {"items": [PageResponse.model_validate(item).model_dump() for item in items], "total": total}
    await set_cache(cache_key, response_data, ttl_seconds=300)
    
    return response_data

@router.get("/{slug}", response_model=PageResponse)
async def get_page(
    slug: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get page by slug (Public)."""
    result = await session.execute(select(PageModel).where(PageModel.slug == slug))
    page = result.scalar_one_or_none()
    if not page:
        raise HTTPException(status_code=404, detail="Page not found")
    return page

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
    if "slug" in update_data:
        update_data["slug"] = slugify(update_data["slug"])
        
    for key, value in update_data.items():
        setattr(page, key, value)
        
    await session.commit()
    await session.refresh(page)
    await delete_cache_pattern("cache:pages:*")
    return page

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


class BulkReassignRequest(BaseModel):
    movie_ids: list[int] = []
    series_ids: list[int] = []
    target_page_ids: list[int] = []
    replace: bool = True

@router.post("/bulk-reassign")
async def bulk_reassign_pages(
    payload: BulkReassignRequest,
    session: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """
    Search & Mark bulk reassignment of movies/series to specific page(s).
    """
    target_pages = []
    if payload.target_page_ids:
        res = await session.execute(select(PageModel).where(PageModel.id.in_(payload.target_page_ids)))
        target_pages = list(res.scalars().all())

    # Update Movies
    if payload.movie_ids:
        from app.infrastructure.db.models.movie import MovieModel
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
        from app.infrastructure.db.models.series import SeriesModel
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

