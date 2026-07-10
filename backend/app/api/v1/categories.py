"""API v1 — Categories endpoints.  Phase 1: CRUD."""
from typing import Sequence
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.api.deps import get_category_service, get_current_admin
from app.application.categories.service import CategoryService
from app.domain.categories.entities import Category

router = APIRouter(prefix="/categories", tags=["categories"])


# ── Schemas ──────────────────────────────────────────────────────
class CategoryCreate(BaseModel):
    name: str
    slug: str
    is_active: bool = True

class CategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    is_active: bool | None = None

class CategoryResponse(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool

    model_config = {"from_attributes": True}


# ── Endpoints ────────────────────────────────────────────────────
@router.post("", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_in: CategoryCreate,
    service: CategoryService = Depends(get_category_service),
    admin: dict = Depends(get_current_admin)
):
    """Create a new category (Admin only)."""
    return await service.create_category(
        name=category_in.name, 
        slug=category_in.slug, 
        is_active=category_in.is_active
    )


@router.get("", response_model=list[CategoryResponse])
async def list_categories(
    skip: int = 0,
    limit: int = 100,
    service: CategoryService = Depends(get_category_service)
):
    """List all categories (Public)."""
    return await service.list_categories(skip=skip, limit=limit)


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(
    category_id: int,
    service: CategoryService = Depends(get_category_service)
):
    """Get category by ID (Public)."""
    category = await service.get_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_in: CategoryUpdate,
    service: CategoryService = Depends(get_category_service),
    admin: dict = Depends(get_current_admin)
):
    """Update a category (Admin only)."""
    category = await service.update_category(
        category_id=category_id,
        name=category_in.name,
        slug=category_in.slug,
        is_active=category_in.is_active
    )
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: int,
    service: CategoryService = Depends(get_category_service),
    admin: dict = Depends(get_current_admin)
):
    """Delete a category (Admin only)."""
    success = await service.delete_category(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
