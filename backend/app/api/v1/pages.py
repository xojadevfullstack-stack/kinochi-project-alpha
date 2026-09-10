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
