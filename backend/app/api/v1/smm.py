"""API v1 — SMM Video Autopilot endpoints (Dual-Mode Settings & Clip Jobs)."""
import hmac
import logging
import os
from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db_session
from app.core.config import settings
from app.infrastructure.db.models.ingest_item import IngestItemModel
from app.infrastructure.db.models.smm import SmmClipJobModel, SmmSettingsModel

logger = logging.getLogger(__name__)
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
    admin_telegram_id: str | None = None


class SmmClipJobCreate(BaseModel):
    media_type: Literal["movie", "series", "episode"] = "movie"
    media_id: int | None = None
    movie_code: str
    title: str
    start_sec: float = 0.0
    duration_sec: float = 45.0
    clip_path: str | None = None
    caption: str | None = None
    generate: bool = False


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


@router.get("/progress")
async def get_smm_progress(db: AsyncSession = Depends(get_db_session), _admin: dict = Depends(get_current_admin)):
    """Return live Cycle 1 (Autopilot ingest) and Cycle 2 (SMM clip) progress snapshot."""
    ingest_counts = dict(
        (
            await db.execute(
                select(IngestItemModel.status, func.count()).group_by(IngestItemModel.status)
            )
        ).all()
    )
    active_ingest = (
        await db.execute(
            select(IngestItemModel)
            .where(IngestItemModel.status == "in_progress")
            .order_by(IngestItemModel.updated_at.desc())
            .limit(1)
        )
    ).scalar_one_or_none()

    job_counts = dict(
        (
            await db.execute(
                select(SmmClipJobModel.status, func.count()).group_by(SmmClipJobModel.status)
            )
        ).all()
    )
    active_jobs = (
        await db.execute(
            select(SmmClipJobModel)
            .where(SmmClipJobModel.status.in_(("generating", "publishing")))
            .order_by(SmmClipJobModel.id.asc())
            .limit(10)
        )
    ).scalars().all()

    return {
        "cycle1": {
            "in_progress": int(ingest_counts.get("in_progress", 0) or 0),
            "queued": int(ingest_counts.get("queued", 0) or 0),
            "published": int(ingest_counts.get("published", 0) or 0),
            "needs_review": int(ingest_counts.get("needs_review", 0) or 0),
            "current_item": (
                {
                    "id": active_ingest.id,
                    "title": active_ingest.title,
                    "source": active_ingest.source,
                    "media_type": active_ingest.media_type,
                }
                if active_ingest
                else None
            ),
        },
        "cycle2": {
            "generating": int(job_counts.get("generating", 0) or 0),
            "waiting_approval": int(job_counts.get("waiting_approval", 0) or 0),
            "scheduled": int(job_counts.get("scheduled", 0) or 0),
            "publishing": int(job_counts.get("publishing", 0) or 0),
            "completed": int(job_counts.get("completed", 0) or 0),
            "failed": int(job_counts.get("failed", 0) or 0),
            "active_jobs": [
                {
                    "id": j.id,
                    "media_type": j.media_type,
                    "movie_code": j.movie_code,
                    "title": j.title,
                    "status": j.status,
                    "progress_pct": int(getattr(j, "progress_pct", 0) or 0),
                    "progress_stage": getattr(j, "progress_stage", None) or "",
                }
                for j in active_jobs
            ],
        },
    }


@router.post("/jobs", status_code=status.HTTP_201_CREATED)
async def create_smm_job(
    payload: SmmClipJobCreate,
    db: AsyncSession = Depends(get_db_session),
    _admin: dict = Depends(get_current_admin),
):
    cfg = await _get_or_create_settings(db)
    if payload.generate:
        initial_status = "generating"
        stage = "Navbatda (klipp kutilmoqda)"
    else:
        initial_status = "scheduled" if cfg.mode == "FULL_AUTO" else "waiting_approval"
        stage = None
    platforms = {p: {"enabled": True, "status": "pending", "post_id": None, "error": None} for p in cfg.enabled_platforms}
    job = SmmClipJobModel(
        **payload.model_dump(exclude={"generate"}),
        status=initial_status,
        progress_pct=0,
        progress_stage=stage,
        platforms_status=platforms,
    )
    db.add(job)
    await db.flush()
    await db.refresh(job)
    return job


async def _apply_approve(db: AsyncSession, job: SmmClipJobModel, req: SmmApproveRequest) -> SmmClipJobModel:
    if req.caption is not None:
        job.caption = req.caption
    if req.scheduled_at is not None:
        job.scheduled_at = req.scheduled_at
    job.status = "publishing" if req.publish_now else "scheduled"
    job.progress_pct = 100
    job.progress_stage = "Kanalga yuborilmoqda" if req.publish_now else "Nashr navbatida"
    await db.flush()
    await db.refresh(job)
    return job


async def _apply_reject(db: AsyncSession, job: SmmClipJobModel) -> SmmClipJobModel:
    job.status = "rejected"
    job.progress_stage = "Rad etilgan"
    await db.flush()
    await db.refresh(job)
    return job


def _verify_bot_secret(x_bot_secret: str | None = Header(default=None, alias="X-Bot-Secret")) -> None:
    if not x_bot_secret or not settings.BOT_API_SECRET or not hmac.compare_digest(
        x_bot_secret.encode(), settings.BOT_API_SECRET.encode()
    ):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Noto'g'ri bot kaliti")


@router.post("/jobs/{job_id}/approve")
async def approve_smm_job(
    job_id: int,
    payload: SmmApproveRequest | None = None,
    db: AsyncSession = Depends(get_db_session),
    _admin: dict = Depends(get_current_admin),
):
    job = await _get_job_or_404(db, job_id)
    return await _apply_approve(db, job, payload or SmmApproveRequest())


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
    job.progress_pct = 0
    job.progress_stage = "Qayta kesish kutilmoqda"
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
    return await _apply_reject(db, job)


@router.post("/bot/jobs/{job_id}/approve")
async def bot_approve_smm_job(
    job_id: int,
    payload: SmmApproveRequest | None = None,
    db: AsyncSession = Depends(get_db_session),
    _: None = Depends(_verify_bot_secret),
):
    job = await _get_job_or_404(db, job_id)
    return await _apply_approve(db, job, payload or SmmApproveRequest())


@router.post("/bot/jobs/{job_id}/reject")
async def bot_reject_smm_job(
    job_id: int,
    db: AsyncSession = Depends(get_db_session),
    _: None = Depends(_verify_bot_secret),
):
    job = await _get_job_or_404(db, job_id)
    return await _apply_reject(db, job)


async def _restore_clip_from_telegram(dest_path: str, storage_msg_id: int) -> bool:
    """Lazily restore rendered clip from Telegram Storage Channel when Render ephemeral disk resets."""
    sess = (os.getenv("SMM_TELEGRAM_STRING_SESSION") or os.getenv("TELEGRAM_STRING_SESSION") or "").strip()
    api_id = settings.TELEGRAM_API_ID
    api_hash = (settings.TELEGRAM_API_HASH or "").strip()
    raw_chat = str(settings.STORAGE_CHANNEL_ID or "").strip()
    if not sess or not api_id or not api_hash or not raw_chat or not storage_msg_id:
        return False
    storage_chat_id: int | str = int(raw_chat) if raw_chat.lstrip("-").isdigit() else raw_chat
    try:
        from telethon import TelegramClient
        from telethon.sessions import StringSession

        os.makedirs(os.path.dirname(os.path.abspath(dest_path)), exist_ok=True)
        client = TelegramClient(StringSession(sess), int(api_id), api_hash)
        await client.connect()
        try:
            msg = await client.get_messages(storage_chat_id, ids=int(storage_msg_id))
            if not msg or not getattr(msg, "media", None):
                return False
            await client.download_media(msg, file=dest_path)
            return os.path.exists(dest_path) and os.path.getsize(dest_path) > 0
        finally:
            await client.disconnect()
    except Exception as exc:
        logger.warning("SMM clip restore from Telegram #%s failed: %s", storage_msg_id, exc)
        return False


@router.get("/jobs/{job_id}/video")
async def stream_smm_job_video(
    job_id: int,
    db: AsyncSession = Depends(get_db_session),
):
    """Serve rendered 9:16 SMM preview MP4 (restoring from Telegram Storage if ephemeral disk cleared)."""
    job = await _get_job_or_404(db, job_id)
    target = (job.clip_path or f"uploads/smm/clip_{job.id}.mp4").strip()
    if not os.path.exists(target) and getattr(job, "clip_storage_message_id", None):
        await _restore_clip_from_telegram(target, int(job.clip_storage_message_id))
    if not os.path.exists(target):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Klipp video fayli topilmadi")
    return FileResponse(target, media_type="video/mp4", filename=f"clip_{job.id}.mp4")
