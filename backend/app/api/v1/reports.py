"""API v1 — Reports (Xatolik haqida xabar berish) endpoints."""
import os
import uuid
import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy import select, func, desc, and_
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
    restore_media: bool = False


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
    telegram_user_id: Optional[int] = None
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
    telegram_user_id: Optional[int] = Form(None),
    file: Optional[UploadFile] = File(None),
    db: AsyncSession = Depends(get_db_session)
):
    """
    Foydalanuvchi tomonidan xatolik haqida xabar yuborish (Anti-spam: 1 so'rov/daqiqa).
    Skrinshot yoki video biriktirish mumkin.
    """
    client_ip = request.client.host if request.client else None
    clean_desc = (description if isinstance(description, str) else "").strip()[:2000]
    tg_user_id = telegram_user_id if isinstance(telegram_user_id, int) else None
    if tg_user_id is None and isinstance(telegram_user_id, str) and telegram_user_id.isdigit():
        tg_user_id = int(telegram_user_id)

    mid = int(movie_id) if (isinstance(movie_id, int) or (isinstance(movie_id, str) and movie_id.isdigit())) else None
    sid = int(series_id) if (isinstance(series_id, int) or (isinstance(series_id, str) and series_id.isdigit())) else None
    eid = int(episode_id) if (isinstance(episode_id, int) or (isinstance(episode_id, str) and episode_id.isdigit())) else None

    saved_file_url = None
    detected_file_type = None
    file_bytes = None
    saved_filename = None

    if isinstance(file, UploadFile) and file.filename:
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

    if media_type == "movie" and mid:
        m_res = await db.execute(select(MovieModel).where(MovieModel.id == mid))
        movie = m_res.scalar_one_or_none()
        if movie:
            valid_movie_id = movie.id
            media_title = movie.title
            site_url = f"https://kinochi.uz/movie/{movie.code}"
    elif media_type in ("series", "episode") or sid or eid:
        if eid:
            ep_res = await db.execute(select(EpisodeModel).where(EpisodeModel.id == eid))
            episode = ep_res.scalar_one_or_none()
            if episode:
                valid_episode_id = episode.id
                valid_series_id = episode.series_id
                seas_res = await db.execute(select(SeasonModel).where(SeasonModel.id == episode.season_id))
                season = seas_res.scalar_one_or_none()
                s_num = season.season_number if season else 1
                ep_info = f"({s_num}-mavsum, {episode.episode_number}-qism)"
                
                s_res = await db.execute(select(SeriesModel).where(SeriesModel.id == episode.series_id))
                series_item = s_res.scalar_one_or_none()
                if series_item:
                    media_title = series_item.title
                    site_url = f"https://kinochi.uz/series/{series_item.id}"
        elif sid:
            s_res = await db.execute(select(SeriesModel).where(SeriesModel.id == sid))
            series_item = s_res.scalar_one_or_none()
            if series_item:
                valid_series_id = series_item.id
                media_title = series_item.title
                site_url = f"https://kinochi.uz/series/{sid}"

    # 1. Per-user / per-IP dedup tekshiruvi (takroriy pending shikoyatni bloklash)
    dedup_cond = [ReportModel.status == "pending", ReportModel.issue_type == issue_type]
    if valid_movie_id:
        dedup_cond.append(ReportModel.movie_id == valid_movie_id)
    elif valid_series_id:
        dedup_cond.append(ReportModel.series_id == valid_series_id)
    elif valid_episode_id:
        dedup_cond.append(ReportModel.episode_id == valid_episode_id)

    if tg_user_id:
        dedup_cond.append(ReportModel.telegram_user_id == tg_user_id)
        dedup_query = select(ReportModel.id).where(and_(*dedup_cond)).limit(1)
    elif client_ip:
        dedup_cond.append(ReportModel.ip_address == client_ip)
        dedup_query = select(ReportModel.id).where(and_(*dedup_cond)).limit(1)
    else:
        dedup_query = None

    if dedup_query is not None:
        existing_report = (await db.execute(dedup_query)).scalar_one_or_none()
        if existing_report:
            raise HTTPException(
                status_code=400,
                detail="Ushbu media bo'yicha shikoyatingiz allaqachon qabul qilingan va ko'rib chiqilmoqda."
            )

    # 2. Shikoyatlar soni chegarasi (Threshold auto-hide: 5 ta shikoyat)
    REPORT_THRESHOLD = 5
    if valid_movie_id:
        cnt_res = await db.execute(
            select(func.count(ReportModel.id)).where(
                ReportModel.movie_id == valid_movie_id,
                ReportModel.status == "pending"
            )
        )
        if (cnt_res.scalar() or 0) + 1 >= REPORT_THRESHOLD:
            m_res = await db.execute(select(MovieModel).where(MovieModel.id == valid_movie_id))
            target_movie = m_res.scalar_one_or_none()
            if target_movie and target_movie.publish_status != "hidden":
                target_movie.publish_status = "hidden"
                logger.warning(f"Kino (ID: {valid_movie_id}) {REPORT_THRESHOLD} ta shikoyat tufayli 'hidden' holatiga o'tkazildi.")
    elif valid_series_id:
        cnt_res = await db.execute(
            select(func.count(ReportModel.id)).where(
                ReportModel.series_id == valid_series_id,
                ReportModel.status == "pending"
            )
        )
        if (cnt_res.scalar() or 0) + 1 >= REPORT_THRESHOLD:
            s_res = await db.execute(select(SeriesModel).where(SeriesModel.id == valid_series_id))
            target_series = s_res.scalar_one_or_none()
            if target_series and target_series.publish_status != "hidden":
                target_series.publish_status = "hidden"
                logger.warning(f"Serial (ID: {valid_series_id}) {REPORT_THRESHOLD} ta shikoyat tufayli 'hidden' holatiga o'tkazildi.")

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
        ip_address=client_ip,
        telegram_user_id=tg_user_id
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
                telegram_user_id=r.telegram_user_id,
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


@router.get("/grouped")
async def list_reports_grouped(
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Shikoyatlarni media bo'yicha guruhlangan holda ko'rish (Faqat admin uchun)."""
    query = (
        select(
            ReportModel.media_type,
            ReportModel.movie_id,
            ReportModel.series_id,
            func.count(ReportModel.id).label("report_count"),
            func.max(ReportModel.created_at).label("latest_report_at")
        )
        .where(ReportModel.status == "pending")
        .group_by(ReportModel.media_type, ReportModel.movie_id, ReportModel.series_id)
        .order_by(desc("report_count"))
    )
    res = await db.execute(query)
    groups = []
    for row in res.all():
        media_type, movie_id, series_id, count, latest_at = row
        title = "Noma'lum"
        code_or_id = None
        if media_type == "movie" and movie_id:
            m_res = await db.execute(select(MovieModel.title, MovieModel.code).where(MovieModel.id == movie_id))
            m_row = m_res.first()
            if m_row:
                title, code_or_id = m_row
        elif media_type in ("series", "episode") and series_id:
            s_res = await db.execute(select(SeriesModel.title).where(SeriesModel.id == series_id))
            s_row = s_res.first()
            if s_row:
                title = s_row[0]
                code_or_id = str(series_id)
        groups.append({
            "media_type": media_type,
            "movie_id": movie_id,
            "series_id": series_id,
            "media_title": title,
            "media_code_or_id": code_or_id,
            "report_count": count,
            "latest_report_at": latest_at.isoformat() if latest_at else None
        })
    return {"groups": groups, "total_groups": len(groups)}


@router.patch("/{report_id}")
async def update_report_status(
    report_id: int,
    data: ReportUpdateStatus,
    db: AsyncSession = Depends(get_db_session),
    admin: dict = Depends(get_current_admin)
):
    """Shikoyat statusini o'zgartirish (pending, resolved, rejected) va mediani tiklash."""
    valid_statuses = {"pending", "resolved", "rejected"}
    if data.status not in valid_statuses:
        raise HTTPException(status_code=400, detail=f"Noto'g'ri status. Ruxsat etilgan: {valid_statuses}")

    r_res = await db.execute(select(ReportModel).where(ReportModel.id == report_id))
    report = r_res.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Shikoyat topilmadi")

    report.status = data.status

    # Mediani qayta tiklash (restore_media)
    if data.restore_media:
        if report.media_type == "movie" and report.movie_id:
            rem_res = await db.execute(
                select(func.count(ReportModel.id)).where(
                    ReportModel.movie_id == report.movie_id,
                    ReportModel.id != report.id,
                    ReportModel.status == "pending"
                )
            )
            if (rem_res.scalar() or 0) == 0:
                m_res = await db.execute(select(MovieModel).where(MovieModel.id == report.movie_id))
                m = m_res.scalar_one_or_none()
                if m and m.publish_status == "hidden":
                    m.publish_status = "published"
                    logger.info(f"Kino (ID: {report.movie_id}) shikoyat hal bo'lgach 'published' holatiga tiklandi.")
        elif report.media_type in ("series", "episode") and report.series_id:
            rem_res = await db.execute(
                select(func.count(ReportModel.id)).where(
                    ReportModel.series_id == report.series_id,
                    ReportModel.id != report.id,
                    ReportModel.status == "pending"
                )
            )
            if (rem_res.scalar() or 0) == 0:
                s_res = await db.execute(select(SeriesModel).where(SeriesModel.id == report.series_id))
                s = s_res.scalar_one_or_none()
                if s and s.publish_status == "hidden":
                    s.publish_status = "published"
                    logger.info(f"Serial (ID: {report.series_id}) shikoyat hal bo'lgach 'published' holatiga tiklandi.")

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
