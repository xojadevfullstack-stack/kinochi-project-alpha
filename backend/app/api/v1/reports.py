"""API v1 — Reports (Xatolik haqida xabar berish) endpoints."""
import os
import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db_session, get_current_admin
from app.api.limiter import limiter
from app.core.config import settings
from app.infrastructure.db.models.report import ReportModel
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel, EpisodeModel, SeasonModel
from app.infrastructure.telegram.telegram_client import telegram_client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/reports", tags=["reports"])

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "reports")
os.makedirs(UPLOAD_DIR, exist_ok=True)

ALLOWED_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_VIDEO_EXTS = {".mp4", ".webm", ".mov"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_VIDEO_SIZE = 50 * 1024 * 1024  # 50 MB

ISSUE_LABELS = {
    "poster_xato": "🖼 Poster noto'g'ri",
    "dublikat": "👥 Dublikat",
    "video_xato": "🎞 Video noto'g'ri",
    "ovoz_xato": "🔇 Ovozda muammo",
    "malumot_xato": "📝 Ma'lumot xato",
    "treyler_xato": "🍿 Treyler ishlamayapti",
    "boshqa": "✍️ Boshqa xatolik"
}


# ── Schemas ──────────────────────────────────────────────────────
class ReportUpdateStatus(BaseModel):
    status: str  # pending | resolved | rejected


class ReportItemResponse(BaseModel):
    id: int
    media_type: str
    movie_id: Optional[int] = None
    series_id: Optional[int] = None
    episode_id: Optional[int] = None
    issue_type: str
    description: Optional[str] = None
    file_url: Optional[str] = None
    file_type: Optional[str] = None
    status: str
    ip_address: Optional[str] = None
    created_at: Optional[str] = None
    media_title: Optional[str] = None
    media_code_or_id: Optional[str] = None

    class Config:
        from_attributes = True


class PaginatedReportsResponse(BaseModel):
    items: List[ReportItemResponse]
    total: int
    pending_count: int


# ── Endpoints ────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
@limiter.limit("1/minute")
async def create_report(
    request: Request,
    media_type: str = Form(...),
    issue_type: str = Form(...),
    movie_id: Optional[int] = Form(None),
    series_id: Optional[int] = Form(None),
    episode_id: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Foydalanuvchi tomonidan xatolik haqida xabar yuborish (Anti-spam: 1 so'rov/daqiqa).
    Skrinshot yoki video biriktirish mumkin.
    """
    client_ip = request.client.host if request.client else None
    clean_desc = (description or "").strip()[:2000]

    saved_file_url = None
    detected_file_type = None
    file_bytes = None
    saved_filename = None

    if file and file.filename:
        _, ext = os.path.splitext(file.filename.lower())
        if ext in ALLOWED_IMAGE_EXTS:
            detected_file_type = "image"
            max_size = MAX_IMAGE_SIZE
        elif ext in ALLOWED_VIDEO_EXTS:
            detected_file_type = "video"
            max_size = MAX_VIDEO_SIZE
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Fayl formati noto'g'ri. Faqat rasm (JPG, PNG, WEBP) yoki video (MP4, WEBM, MOV) ruxsat etilgan."
            )

        file_bytes = await file.read()
        if len(file_bytes) > max_size:
            size_mb = max_size // (1024 * 1024)
            raise HTTPException(
                status_code=400,
                detail=f"Fayl hajmi juda katta. Maksimal ruxsat etilgan hajm: {size_mb} MB"
            )

        saved_filename = f"{uuid.uuid4().hex[:12]}{ext}"
        filepath = os.path.join(UPLOAD_DIR, saved_filename)
        try:
            with open(filepath, "wb") as f:
                f.write(file_bytes)
            saved_file_url = f"/uploads/reports/{saved_filename}"
        except Exception as e:
            logger.error(f"Faylni saqlashda xatolik: {e}")
            raise HTTPException(status_code=500, detail="Faylni saqlashda xatolik yuz berdi")

    # Media ma'lumotlarini qidirish va ID larni tekshirish
    media_title = "Noma'lum"
    ep_info = ""
    site_url = "https://kinochi.uz"
    valid_movie_id = None
    valid_series_id = None
    valid_episode_id = None

    if media_type == "movie" and movie_id:
        m_res = await db.execute(select(MovieModel).where(MovieModel.id == movie_id))
        movie = m_res.scalar_one_or_none()
        if movie:
            valid_movie_id = movie.id
            media_title = movie.title
            site_url = f"https://kinochi.uz/movie/{movie.code}"
    elif media_type == "series" and series_id:
        s_res = await db.execute(select(SeriesModel).where(SeriesModel.id == series_id))
        series_item = s_res.scalar_one_or_none()
        if series_item:
            valid_series_id = series_item.id
            media_title = series_item.title
            site_url = f"https://kinochi.uz/series/{series_id}"

        if episode_id:
            ep_res = await db.execute(select(EpisodeModel).where(EpisodeModel.id == episode_id))
            episode = ep_res.scalar_one_or_none()
            if episode:
                valid_episode_id = episode.id
                seas_res = await db.execute(select(SeasonModel).where(SeasonModel.id == episode.season_id))
                season = seas_res.scalar_one_or_none()
                s_num = season.season_number if season else 1
                ep_info = f"({s_num}-mavsum, {episode.episode_number}-qism)"

    # DB ga saqlash
    report = ReportModel(
        media_type=media_type,
        movie_id=valid_movie_id,
        series_id=valid_series_id,
        episode_id=valid_episode_id,
        issue_type=issue_type,
        description=clean_desc,
        file_url=saved_file_url,
        file_type=detected_file_type,
        status="pending",
        ip_address=client_ip
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)

    issue_label = ISSUE_LABELS.get(issue_type, issue_type)
    file_label = "Mavjud emas"
    if detected_file_type == "image":
        file_label = "📸 Skrinshot mavjud"
    elif detected_file_type == "video":
        file_label = "🎥 Video mavjud"

    # Telegram xabari formati
    caption = (
        f"🚨 <b>SAYTDAN XATOLIK BO'YICHA XABAR!</b>\n"
        f"🎬 <b>Media:</b> \"{media_title}\" {ep_info}\n"
        f"⚠️ <b>Muammo turi:</b> {issue_label}\n"
        f"💬 <b>User izohi:</b> \"{clean_desc or 'Izoh qoldirilmadi'}\"\n"
        f"📎 <b>Biriktirildi:</b> {file_label}\n"
        f"🔗 <b>Sayt:</b> {site_url}"
    )

    admin_chat_id = settings.AUTO_TOPIC_CHAT_ID or settings.STORAGE_CHANNEL_ID
    if admin_chat_id:
        try:
            if detected_file_type == "image" and file_bytes and saved_filename:
                await telegram_client.send_photo(
                    chat_id=admin_chat_id,
                    photo_bytes=file_bytes,
                    filename=saved_filename,
                    caption=caption
                )
            elif detected_file_type == "video" and file_bytes and saved_filename:
                await telegram_client.send_video(
                    chat_id=admin_chat_id,
                    video_bytes=file_bytes,
                    filename=saved_filename,
                    caption=caption
                )
            else:
                await telegram_client.send_message(
                    chat_id=admin_chat_id,
                    text=caption
                )
        except Exception as tg_err:
            logger.warning(f"Telegramga shikoyat xabarini yuborishda xatolik: {tg_err}")

    return {
        "status": "success",
        "message": "Xatolik haqidagi xabaringiz qabul qilindi. Tez orada ko'rib chiqamiz!",
        "report_id": report.id
    }


@router.get("", response_model=PaginatedReportsResponse)
async def list_reports(
    status_filter: Optional[str] = Query(None, alias="status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Barcha shikoyatlarni ko'rish (Faqat admin uchun)."""
    base_query = select(ReportModel)
    if status_filter:
        base_query = base_query.where(ReportModel.status == status_filter)

    total_stmt = select(func.count(ReportModel.id))
    if status_filter:
        total_stmt = total_stmt.where(ReportModel.status == status_filter)
    total = (await db.execute(total_stmt)).scalar() or 0

    pending_stmt = select(func.count(ReportModel.id)).where(ReportModel.status == "pending")
    pending_count = (await db.execute(pending_stmt)).scalar() or 0

    query = base_query.order_by(desc(ReportModel.id)).offset(skip).limit(limit)
    res = await db.execute(query)
    reports = res.scalars().all()

    items = []
    for r in reports:
        media_title = None
        code_or_id = None
        if r.media_type == "movie" and r.movie_id:
            m_res = await db.execute(select(MovieModel.title, MovieModel.code).where(MovieModel.id == r.movie_id))
            row = m_res.first()
            if row:
                media_title, code_or_id = row
        elif r.media_type == "series" and r.series_id:
            s_res = await db.execute(select(SeriesModel.title).where(SeriesModel.id == r.series_id))
            row = s_res.first()
            if row:
                media_title = row[0]
                code_or_id = str(r.series_id)

        items.append(
            ReportItemResponse(
                id=r.id,
                media_type=r.media_type,
                movie_id=r.movie_id,
                series_id=r.series_id,
                episode_id=r.episode_id,
                issue_type=r.issue_type,
                description=r.description,
                file_url=r.file_url,
                file_type=r.file_type,
                status=r.status,
                ip_address=r.ip_address,
                created_at=r.created_at.isoformat() if r.created_at else None,
                media_title=media_title,
                media_code_or_id=code_or_id
            )
        )

    return PaginatedReportsResponse(
        items=items,
        total=total,
        pending_count=pending_count
    )


@router.patch("/{report_id}")
async def update_report_status(
    report_id: int,
    data: ReportUpdateStatus,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Shikoyat statusini o'zgartirish (pending, resolved, rejected)."""
    valid_statuses = {"pending", "resolved", "rejected"}
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Noto'g'ri status. Ruxsat etilgan: {valid_statuses}")

    r_res = await db.execute(select(ReportModel).where(ReportModel.id == report_id))
    report = r_res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Shikoyat topilmadi")

    report.status = data.status
    await db.commit()
    await db.refresh(report)

    return {"status": "ok", "report_id": report.id, "new_status": report.status}


@router.delete("/{report_id}")
async def delete_report(
    report_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Shikoyatni o'chirish."""
    r_res = await db.execute(select(ReportModel).where(ReportModel.id == report_id))
    report = r_res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Shikoyat topilmadi")

    if report.file_url and report.file_url.startswith("/uploads/reports/"):
        filename = os.path.basename(report.file_url)
        filepath = os.path.join(UPLOAD_DIR, filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except Exception:
                pass

    await db.delete(report)
    await db.commit()
    return {"status": "ok", "deleted_id": report_id}
