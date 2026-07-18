from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db_session, get_current_admin
from app.infrastructure.db.models.page import PageModel

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
    model = PageModel(**page_in.model_dump())
    session.add(model)
    await session.commit()
    await session.refresh(model)
    return model

@router.get("", response_model=PaginatedPagesResponse)
async def list_pages(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    session: AsyncSession = Depends(get_db_session)
):
    """List all pages (Public)."""
    from sqlalchemy import func
    
    count_query = select(func.count()).select_from(PageModel)
    total = await session.scalar(count_query)
    
    query = select(PageModel).offset(skip).limit(limit)
    result = await session.execute(query)
    items = result.scalars().all()
    
    return {"items": items, "total": total}

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
    for key, value in update_data.items():
        setattr(page, key, value)
        
    await session.commit()
    await session.refresh(page)
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
