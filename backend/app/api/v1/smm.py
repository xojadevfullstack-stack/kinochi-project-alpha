"""API v1 — SMM Video Autopilot endpoints (Dual-Mode Settings & Clip Jobs)."""
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db_session
from app.infrastructure.db.models.smm import SmmClipJobModel, SmmSettingsModel

router = APIRouter(prefix="/smm", tags=["smm"])


class SmmSettingsUpdate(BaseModel):
    mode: Literal["SEMI_AUTO", "FULL_AUTO"] | None = None
    clip_duration_sec: int | None = Field(default=None, ge=15, le=90)
    daily_limit: int | None = Field(default=None, ge=1, le=50)
    schedule_hours: list[str] | None = None
    enabled_platforms: list[str] | None = None
    auto_pick_from_catalog: bool | None = None
    copyright_shield: bool | None = None
    bot_username: str | None = None
    telegram_channel_id: str | None = None


class SmmClipJobCreate(BaseModel):
    media_type: Literal["movie", "series"] = "movie"
    media_id: int | None = None
    movie_code: str
    title: str
    start_sec: float = 0.0
    duration_sec: float = 45.0
    clip_path: str | None = None
    caption: str | None = None


class SmmApproveRequest(BaseModel):
    publish_now: bool = False
    scheduled_at: datetime | None = None
    caption: str | None = None


class SmmRecutRequest(BaseModel):
    start_sec: float = Field(ge=0.0)
    duration_sec: float = Field(default=45.0, ge=10.0, le=90.0)


async def _get_or_create_settings(db: AsyncSession) -> SmmSettingsModel:
    row = (await db.execute(select(SmmSettingsModel).where(SmmSettingsModel.id == 1))).scalar_one_or_none()
    if row is None:
        row = SmmSettingsModel(id=1)
        db.add(row)
        await db.flush()
    return row


async def _get_job_or_404(db: AsyncSession, job_id: int) -> SmmClipJobModel:
    job = (await db.execute(select(SmmClipJobModel).where(SmmClipJobModel.id == job_id))).scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="SMM clip job topilmadi")
    return job


@router.get("/settings")
async def get_smm_settings(db: AsyncSession = Depends(get_db_session), _admin: dict = Depends(get_current_admin)):
    return await _get_or_create_settings(db)


@router.put("/settings")
async def update_smm_settings(
    payload: SmmSettingsUpdate,
    db: AsyncSession = Depends(get_db_session),
    _admin: dict = Depends(get_current_admin),
):
    row = await _get_or_create_settings(db)
    for field, val in payload.model_dump(exclude_unset=True).items():
        setattr(row, field, val)
    await db.flush()
    await db.refresh(row)
    return row


@router.get("/jobs")
async def list_smm_jobs(
    status_filter: str | None = Query(default=None, alias="status"),
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db_session),
    _admin: dict = Depends(get_current_admin),
):
    stmt = select(SmmClipJobModel).order_by(SmmClipJobModel.id.desc()).limit(limit)
    if status_filter and status_filter != "all":
        stmt = stmt.where(SmmClipJobModel.status == status_filter)
    return (await db.execute(stmt)).scalars().all()


@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def create_smm_job(
    payload: SmmClipJobCreate,
    db: AsyncSession = Depends(get_db_session),
    _admin: dict = Depends(get_current_admin),
):
    cfg = await _get_or_create_settings(db)
    initial_status = "scheduled" if cfg.mode == "FULL_AUTO" else "waiting_approval"
    platforms = {p: {"enabled": True, "status": "pending", "post_id": None, "error": None} for p in cfg.enabled_platforms}
    job = SmmClipJobModel(**payload.model_dump(), status=initial_status, platforms_status=platforms)
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


@router.post("/jobs/{job_id}/approve")
async def approve_smm_job(
    job_id: int,
    payload: SmmApproveRequest | None = None,
    db: AsyncSession = Depends(get_db_session),
    _admin: dict = Depends(get_current_admin),
):
    job = await _get_job_or_404(db, job_id)
    req = payload or SmmApproveRequest()
    if req.caption is not None:
        job.caption = req.caption
    if req.scheduled_at is not None:
        job.scheduled_at = req.scheduled_at
    job.status = "publishing" if req.publish_now else "scheduled"
    await db.flush()
    await db.refresh(job)
    return job


@router.post("/jobs/{job_id}/recut")
async def recut_smm_job(
    job_id: int,
    payload: SmmRecutRequest,
    db: AsyncSession = Depends(get_db_session),
    _admin: dict = Depends(get_current_admin),
):
    job = await _get_job_or_404(db, job_id)
    job.start_sec = payload.start_sec
    job.duration_sec = payload.duration_sec
    job.status = "generating"
    await db.flush()
    await db.refresh(job)
    return job


@router.post("/jobs/{job_id}/reject")
async def reject_smm_job(
    job_id: int,
    db: AsyncSession = Depends(get_db_session),
    _admin: dict = Depends(get_current_admin),
):
    job = await _get_job_or_404(db, job_id)
    job.status = "rejected"
    await db.flush()
    await db.refresh(job)
    return job
