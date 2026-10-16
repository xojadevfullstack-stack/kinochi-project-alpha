"""
API v1 — Rejected Items endpoints.
Admission Gate tomonidan rad etilgan kontentlarni boshqarish va qayta urinish (Admin).
"""
import logging
from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db_session
from app.api.limiter import limiter
from app.infrastructure.db.models.rejected_item import RejectedItemModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rejected", tags=["rejected"])


class RejectedItemResponse(BaseModel):
    id: int
    media_type: str
    source: str
    source_key: str
    title: str
    payload: dict[str, Any]
    defects: list[dict[str, Any]]
    media_id: Optional[int] = None
    attempts: int
    status: str
    created_at: Any
    updated_at: Any

    class Config:
        from_attributes = True


class PaginatedRejectedResponse(BaseModel):
    items: List[RejectedItemResponse]
    total: int


@router.get("", response_model=PaginatedRejectedResponse)
@limiter.limit("60/minute")
async def list_rejected_items(
    request: Request,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    source: Optional[str] = None,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Rad etilgan elementlar ro'yxatini olish (Admin)."""
    stmt = select(RejectedItemModel)
    if status_filter:
        stmt = stmt.where(RejectedItemModel.status == status_filter)
    if source:
        stmt = stmt.where(RejectedItemModel.source == source)

    count_stmt = select(func.count(RejectedItemModel.id))
    if status_filter:
        count_stmt = count_stmt.where(RejectedItemModel.status == status_filter)
    if source:
        count_stmt = count_stmt.where(RejectedItemModel.source == source)

    total_res = await db.scalar(count_stmt)
    total = total_res or 0

    stmt = stmt.order_by(desc(RejectedItemModel.updated_at)).offset(skip).limit(limit)
    res = await db.execute(stmt)
    items = res.scalars().all()

    return {"items": items, "total": total}


@router.post("/{item_id}/retry")
@limiter.limit("20/minute")
async def retry_rejected_item(
    request: Request,
    item_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Rad etilgan elementni qayta ishlashga jo'natish (Admin)."""
    item = await db.get(RejectedItemModel, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Rejected item topilmadi")

    # Statusini 'resolved' yoki 'pending' qilib qayta urinishga ruxsat berish
    item.status = "resolved"
    item.updated_at = func.now()

    # S5 / SF-003: Agar bu element tmdb_seed bo'lsa, seed_candidates holatini ham 'new' ga qaytarish
    if item.source == "tmdb_seed" and item.source_key and item.source_key.startswith("tmdb:"):
        parts = item.source_key.split(":")
        if len(parts) >= 3 and parts[2].isdigit():
            cand_kind = parts[1]
            cand_tmdb_id = int(parts[2])
            from app.infrastructure.db.models.seed_candidate import SeedCandidateModel
            stmt_cand = select(SeedCandidateModel).where(
                SeedCandidateModel.kind == cand_kind,
                SeedCandidateModel.tmdb_id == cand_tmdb_id
            )
            cand_res = await db.execute(stmt_cand)
            cand = cand_res.scalar_one_or_none()
            if cand:
                cand.status = "new"
                cand.attempts = 0
                cand.updated_at = func.now()

    await db.commit()

    logger.info(f"Admin {admin.get('username')} tomonidan rejected item {item_id} qayta urinishga ruxsat berildi.")
    return {"message": "Item muvaffaqiyatli qayta urinish holatiga o'tkazildi", "id": item_id}


@router.post("/{item_id}/blacklist")
@limiter.limit("20/minute")
async def blacklist_rejected_item(
    request: Request,
    item_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Rad etilgan elementni butunlay qora ro'yxatga kiritish (Admin)."""
    item = await db.get(RejectedItemModel, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Rejected item topilmadi")

    item.status = "blacklisted"
    item.updated_at = func.now()
    await db.commit()

    logger.info(f"Admin {admin.get('username')} tomonidan rejected item {item_id} blacklisted qilindi.")
    return {"message": "Item qora ro'yxatga kiritildi", "id": item_id}
