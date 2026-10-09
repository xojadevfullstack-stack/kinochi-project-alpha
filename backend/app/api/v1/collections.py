"""
API v1 — Collections and Franchises endpoints.
Supports Dual Timeline Ordering (Chronological Story vs Release Date).
"""
from datetime import datetime
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import select, func, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_db_session, get_current_admin
from app.api.limiter import limiter
from app.infrastructure.db.models.collection import CollectionModel, CollectionItemModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel
from app.core.cache import get_cache, set_cache, delete_cache_pattern

router = APIRouter(prefix="/collections", tags=["collections"])


# ── Schemas ──────────────────────────────────────────────────────
class CollectionItemMovieSummary(BaseModel):
    id: int
    title: str
    original_title: str | None = None
    code: str
    poster_url: str | None = None
    release_year: int | None = None
    imdb_rating: float | None = None
    model_config = {"from_attributes": True}


class CollectionItemSeriesSummary(BaseModel):
    id: int
    title: str
    poster_url: str | None = None
    release_year: int | None = None
    imdb_rating: float | None = None
    model_config = {"from_attributes": True}


class CollectionItemResponse(BaseModel):
    id: int
    collection_id: int
    movie_id: int | None = None
    series_id: int | None = None
    chronological_order: int
    release_order: int
    timeline_event_desc: str | None = None
    is_locked: bool
    movie: CollectionItemMovieSummary | None = None
    series: CollectionItemSeriesSummary | None = None
    model_config = {"from_attributes": True}


class CollectionResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None = None
    poster_url: str | None = None
    banner_url: str | None = None
    is_franchise: bool
    is_active: bool
    sort_order: int
    items_count: int = 0
    model_config = {"from_attributes": True}


class CollectionDetailResponse(CollectionResponse):
    items: list[CollectionItemResponse] = []


class MovieFranchiseContextResponse(BaseModel):
    collection_id: int
    collection_name: str
    collection_slug: str
    is_franchise: bool
    current_chronological_order: int
    current_release_order: int
    timeline_event_desc: str | None = None
    total_parts: int
    prev_item: CollectionItemResponse | None = None
    next_item: CollectionItemResponse | None = None
    timeline_items: list[CollectionItemResponse] = []


class CollectionCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    poster_url: str | None = None
    banner_url: str | None = None
    is_franchise: bool = True
    is_active: bool = True
    sort_order: int = 0


class CollectionUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    poster_url: str | None = None
    banner_url: str | None = None
    is_franchise: bool | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class CollectionItemCreate(BaseModel):
    movie_id: int | None = None
    series_id: int | None = None
    chronological_order: int = 1
    release_order: int = 1
    timeline_event_desc: str | None = None
    is_locked: bool = True


class CollectionItemUpdate(BaseModel):
    chronological_order: int | None = None
    release_order: int | None = None
    timeline_event_desc: str | None = None
    is_locked: bool | None = None


# ── Public Endpoints ─────────────────────────────────────────────
@router.get("", response_model=list[CollectionResponse])
@limiter.limit("120/minute")
async def list_collections(
    request: Request,
    franchise_only: bool = False,
    db: AsyncSession = Depends(get_db_session),
):
    """List all active collections / cinematic franchises (Public)."""
    cache_key = f"cache:collections:list:{franchise_only}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    query = select(CollectionModel).where(CollectionModel.is_active == True)
    if franchise_only:
        query = query.where(CollectionModel.is_franchise == True)
    query = query.order_by(CollectionModel.sort_order.asc(), CollectionModel.id.asc())

    result = await db.execute(query)
    collections = result.scalars().all()

    # Calculate item counts
    resp = []
    for c in collections:
        count_res = await db.execute(
            select(func.count(CollectionItemModel.id)).where(CollectionItemModel.collection_id == c.id)
        )
        count = count_res.scalar_one() or 0
        resp.append(
            CollectionResponse(
                id=c.id,
                name=c.name,
                slug=c.slug,
                description=c.description,
                poster_url=c.poster_url,
                banner_url=c.banner_url,
                is_franchise=c.is_franchise,
                is_active=c.is_active,
                sort_order=c.sort_order,
                items_count=count,
            )
        )

    response_data = [item.model_dump(mode="json") for item in resp]
    await set_cache(cache_key, response_data, 300)
    return resp


@router.get("/{slug_or_id}", response_model=CollectionDetailResponse)
@limiter.limit("120/minute")
async def get_collection(
    request: Request,
    slug_or_id: str,
    sort: Literal["chronological", "release"] = "chronological",
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get collection details and ordered items (Public).
    Supports ?sort=chronological (Story Timeline) vs ?sort=release (Release Date).
    """
    cache_key = f"cache:collections:detail:{slug_or_id}:{sort}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    query = select(CollectionModel)
    if slug_or_id.isdigit():
        query = query.where(CollectionModel.id == int(slug_or_id))
    else:
        query = query.where(CollectionModel.slug == slug_or_id)

    result = await db.execute(query)
    collection = result.scalar_one_or_none()
    if not collection:
        raise HTTPException(status_code=404, detail="To'plam topilmadi")

    # Fetch ordered items
    items_query = (
        select(CollectionItemModel)
        .where(CollectionItemModel.collection_id == collection.id)
        .options(
            selectinload(CollectionItemModel.movie),
            selectinload(CollectionItemModel.series),
        )
    )

    if sort == "release":
        items_query = items_query.order_by(CollectionItemModel.release_order.asc(), CollectionItemModel.id.asc())
    else:
        items_query = items_query.order_by(CollectionItemModel.chronological_order.asc(), CollectionItemModel.id.asc())

    items_res = await db.execute(items_query)
    items = items_res.scalars().all()

    detail = CollectionDetailResponse(
        id=collection.id,
        name=collection.name,
        slug=collection.slug,
        description=collection.description,
        poster_url=collection.poster_url,
        banner_url=collection.banner_url,
        is_franchise=collection.is_franchise,
        is_active=collection.is_active,
        sort_order=collection.sort_order,
        items_count=len(items),
        items=[CollectionItemResponse.model_validate(it) for it in items],
    )

    response_data = detail.model_dump(mode="json")
    await set_cache(cache_key, response_data, 300)
    return detail


@router.get("/movie-context/{movie_code}", response_model=MovieFranchiseContextResponse | None)
@limiter.limit("120/minute")
async def get_movie_franchise_context(
    request: Request,
    movie_code: str,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Get franchise chronology context for a specific movie.
    Used by movie details page & video player for the Timeline Bar and Next Movie navigation!
    """
    cache_key = f"cache:collections:movie-ctx:{movie_code}"
    cached = await get_cache(cache_key)
    if cached:
        return cached

    # Find movie by code
    movie_res = await db.execute(select(MovieModel).where(MovieModel.code == movie_code.upper()))
    movie = movie_res.scalar_one_or_none()
    if not movie:
        raise HTTPException(status_code=404, detail="Kino topilmadi")

    # Find franchise collection item
    item_res = await db.execute(
        select(CollectionItemModel)
        .where(CollectionItemModel.movie_id == movie.id)
        .options(selectinload(CollectionItemModel.collection))
    )
    current_item = item_res.scalars().first()
    if not current_item or not current_item.collection:
        return None

    col = current_item.collection

    # Fetch all items in this collection ordered chronologically
    all_items_res = await db.execute(
        select(CollectionItemModel)
        .where(CollectionItemModel.collection_id == col.id)
        .options(
            selectinload(CollectionItemModel.movie),
            selectinload(CollectionItemModel.series),
        )
        .order_by(CollectionItemModel.chronological_order.asc(), CollectionItemModel.id.asc())
    )
    all_items = all_items_res.scalars().all()

    # Determine prev and next items
    current_idx = -1
    for i, it in enumerate(all_items):
        if it.id == current_item.id:
            current_idx = i
            break

    prev_item = all_items[current_idx - 1] if current_idx > 0 else None
    next_item = all_items[current_idx + 1] if current_idx >= 0 and current_idx < len(all_items) - 1 else None

    context = MovieFranchiseContextResponse(
        collection_id=col.id,
        collection_name=col.name,
        collection_slug=col.slug,
        is_franchise=col.is_franchise,
        current_chronological_order=current_item.chronological_order,
        current_release_order=current_item.release_order,
        timeline_event_desc=current_item.timeline_event_desc,
        total_parts=len(all_items),
        prev_item=CollectionItemResponse.model_validate(prev_item) if prev_item else None,
        next_item=CollectionItemResponse.model_validate(next_item) if next_item else None,
        timeline_items=[CollectionItemResponse.model_validate(it) for it in all_items],
    )

    response_data = context.model_dump(mode="json")
    await set_cache(cache_key, response_data, 300)
    return context


# ── Admin Endpoints ──────────────────────────────────────────────
@router.post("", response_model=CollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    data: CollectionCreate,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """Create a new collection or franchise (Admin only)."""
    # Check if slug exists
    exists_res = await db.execute(select(CollectionModel).where(CollectionModel.slug == data.slug))
    if exists_res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Bunday slug'li to'plam allaqachon mavjud")

    col = CollectionModel(**data.model_dump())
    db.add(col)
    await db.commit()
    await db.refresh(col)
    await delete_cache_pattern("cache:collections:*")
    return CollectionResponse.model_validate(col)


@router.put("/{collection_id}", response_model=CollectionResponse)
async def update_collection(
    collection_id: int,
    data: CollectionUpdate,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """Update collection details (Admin only)."""
    col = await db.get(CollectionModel, collection_id)
    if not col:
        raise HTTPException(status_code=404, detail="To'plam topilmadi")

    update_dict = data.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(col, k, v)

    await db.commit()
    await db.refresh(col)
    await delete_cache_pattern("cache:collections:*")
    return CollectionResponse.model_validate(col)


@router.delete("/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """Delete a collection and its items (Admin only)."""
    col = await db.get(CollectionModel, collection_id)
    if not col:
        raise HTTPException(status_code=404, detail="To'plam topilmadi")

    await db.delete(col)
    await db.commit()
    await delete_cache_pattern("cache:collections:*")
    return None


@router.post("/{collection_id}/items", response_model=CollectionItemResponse, status_code=status.HTTP_201_CREATED)
async def add_item_to_collection(
    collection_id: int,
    data: CollectionItemCreate,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """Add a movie or series to a collection (Admin only)."""
    col = await db.get(CollectionModel, collection_id)
    if not col:
        raise HTTPException(status_code=404, detail="To'plam topilmadi")

    item = CollectionItemModel(collection_id=collection_id, **data.model_dump())
    db.add(item)
    await db.commit()
    await db.refresh(item)
    await delete_cache_pattern("cache:collections:*")
    return CollectionItemResponse.model_validate(item)


@router.put("/items/{item_id}", response_model=CollectionItemResponse)
async def update_collection_item(
    item_id: int,
    data: CollectionItemUpdate,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """Update ordering or lock status of an item (Admin only)."""
    item = await db.get(CollectionItemModel, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="To'plam elementi topilmadi")

    update_dict = data.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(item, k, v)

    await db.commit()
    await db.refresh(item)
    await delete_cache_pattern("cache:collections:*")
    return CollectionItemResponse.model_validate(item)


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection_item(
    item_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin),
):
    """Remove an item from a collection (Admin only)."""
    item = await db.get(CollectionItemModel, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="To'plam elementi topilmadi")

    await db.delete(item)
    await db.commit()
    await delete_cache_pattern("cache:collections:*")
    return None
