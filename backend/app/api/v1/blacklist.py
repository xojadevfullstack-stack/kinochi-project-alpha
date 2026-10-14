import logging
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from datetime import datetime

from app.api.deps import get_db_session, get_current_admin
from app.infrastructure.db.models.blacklist import BlacklistModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/blacklist", tags=["blacklist"])


class BlacklistCreate(BaseModel):
    title: str | None = None
    url: str | None = None
    reason: str | None = "Buzilgan / bo'sh kontent"

class BlacklistItemResponse(BaseModel):
    id: int
    title: str | None = None
    url: str | None = None
    reason: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}

class PaginatedBlacklistResponse(BaseModel):
    items: list[BlacklistItemResponse]
    total: int


@router.get("", response_model=PaginatedBlacklistResponse)
async def list_blacklist(
    q: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """List all blacklisted movies and series (Admin only)."""
    stmt = select(BlacklistModel)
    count_stmt = select(func.count()).select_from(BlacklistModel)

    if q and q.strip():
        term = f"%{q.strip()}%"
        where_cond = or_(
            BlacklistModel.title.ilike(term),
            BlacklistModel.url.ilike(term),
            BlacklistModel.reason.ilike(term)
        )
        stmt = stmt.where(where_cond)
        count_stmt = count_stmt.where(where_cond)

    total = await db.scalar(count_stmt) or 0
    stmt = stmt.order_by(BlacklistModel.id.desc()).offset(skip).limit(limit)
    res = await db.execute(stmt)
    items = res.scalars().all()

    return {
        "items": [BlacklistItemResponse.model_validate(it) for it in items],
        "total": total
    }


@router.post("", response_model=BlacklistItemResponse, status_code=status.HTTP_201_CREATED)
async def add_to_blacklist(
    item_in: BlacklistCreate,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Add a title or URL to blacklist (Admin only)."""
    if not item_in.title and not item_in.url:
        raise HTTPException(status_code=400, detail="Nom yoki URL manzil kiritilishi shart.")

    # Check for existing
    where_conds = []
    if item_in.title and item_in.title.strip():
        where_conds.append(func.lower(BlacklistModel.title) == item_in.title.strip().lower())
    if item_in.url and item_in.url.strip():
        where_conds.append(func.lower(BlacklistModel.url) == item_in.url.strip().lower())

    if where_conds:
        stmt = select(BlacklistModel).where(or_(*where_conds))
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            return existing

    model = BlacklistModel(
        title=item_in.title.strip() if item_in.title else None,
        url=item_in.url.strip() if item_in.url else None,
        reason=item_in.reason.strip() if item_in.reason else "Buzilgan / bo'sh kontent"
    )
    db.add(model)
    await db.commit()
    await db.refresh(model)
    return model


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_from_blacklist(
    item_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Remove item from blacklist (White-list / Re-allow) (Admin only)."""
    item = await db.get(BlacklistModel, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Qora ro'yxatdan topilmadi")
    await db.delete(item)
    await db.commit()


@router.get("/check")
async def check_is_blacklisted(
    title: str | None = None,
    url: str | None = None,
    db: AsyncSession = Depends(get_db_session)
):
    """Check if title or url matches any blacklist entry (Public/Internal for Scraper)."""
    if not title and not url:
        return {"blacklisted": False}

    conditions = []
    if title:
        conditions.append(func.lower(BlacklistModel.title) == title.strip().lower())
    if url:
        conditions.append(func.lower(BlacklistModel.url) == url.strip().lower())

    stmt = select(BlacklistModel).where(or_(*conditions))
    res = await db.execute(stmt)
    item = res.scalar_one_or_none()
    if item:
        return {"blacklisted": True, "reason": item.reason, "item_id": item.id}
    return {"blacklisted": False}
