import os
import sys
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field

from app.api.deps import get_current_admin

logger = logging.getLogger(__name__)

# The scraper lives next to backend/ (project root). In the production Docker image
# only backend/ is copied, so the import must be optional: the rest of the API
# must keep working and these endpoints answer 503 with a clear message.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from scraper.queue_manager import QueueManager
    from scraper.process_manager import ProcessManager
    SCRAPER_AVAILABLE = True
except Exception as _exc:  # pragma: no cover
    QueueManager = None  # type: ignore
    ProcessManager = None  # type: ignore
    SCRAPER_AVAILABLE = False
    logger.warning(f"Scraper moduli yuklanmadi (faqat lokal kompyuterda ishlaydi): {_exc}")


def require_scraper(admin=Depends(get_current_admin)):
    if not SCRAPER_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Parser & Grabber faqat scraper papkasi mavjud bo'lgan lokal serverda ishlaydi.",
        )
    return admin


router = APIRouter(prefix="/scraper", tags=["scraper"])

SOURCES = ("uzmovi", "asilmedia")
MEDIA_TYPES = ("all", "movie", "series")
STATUSES = ("pending", "in_progress", "completed", "failed", "already_exists")


class ParseRequest(BaseModel):
    source: str = Field("uzmovi", description="Manba: uzmovi yoki asilmedia")
    pages: int = Field(3, ge=1, le=20, description="Sahifalar soni")


class DownloadRequest(BaseModel):
    target: str = Field("uzmovi", description="Maqsadli bot: uzmovi yoki asilmedia")
    limit: int = Field(5, ge=1, le=100, description="Yuklanadigan kinolar soni")
    codes: Optional[str] = Field(None, max_length=500, description="Muayyan film kodlari (masalan: 15 yoki 1-5 yoki 10,15)")
    media_type: str = Field("all", description="all, movie yoki series")


class StatusResponse(BaseModel):
    is_running: bool
    task_type: str
    current_action: str
    current_item: Optional[Dict[str, Any]] = None
    progress: Dict[str, Any]
    started_at: Optional[str] = None
    elapsed_seconds: int = 0
    logs: List[Dict[str, Any]]
    stats: Dict[str, int]


def _ensure_ok(res: Dict[str, Any]) -> Dict[str, Any]:
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message", "Xatolik"))
    return res


# NOTE: plain `def` handlers run in FastAPI's threadpool, so file IO / process
# bookkeeping never blocks the event loop.

@router.get("/status", response_model=StatusResponse)
def get_status(admin=Depends(require_scraper)):
    """Scraper jarayonining hozirgi holati, progressi va loglarini olish."""
    return ProcessManager().get_status()


@router.get("/queue")
def get_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query("all"),
    source: Optional[str] = Query("all"),
    search: Optional[str] = Query(None, max_length=200),
    admin=Depends(require_scraper),
):
    """Scraper navbatidagi filmlar va seriallar ro'yxatini olish."""
    if status and status != "all" and status not in STATUSES:
        raise HTTPException(status_code=400, detail="Noto'g'ri status filtri")
    if source and source != "all" and source not in SOURCES:
        raise HTTPException(status_code=400, detail="Noto'g'ri manba filtri")

    qm = QueueManager()
    skip = (page - 1) * page_size
    items, total_count = qm.get_filtered(status=status, source=source, search=search, skip=skip, limit=page_size)
    total_pages = max(1, (total_count + page_size - 1) // page_size)

    return {
        "items": [item.__dict__ for item in items],
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "stats": qm.stats(),
    }


@router.post("/start-parse")
def start_parse(data: ParseRequest, admin=Depends(require_scraper)):
    """Saytdan katalog yig'ish (Parse) jarayonini ishga tushirish."""
    if data.source not in SOURCES:
        raise HTTPException(status_code=400, detail="Noma'lum manba")
    return _ensure_ok(ProcessManager().start_parse(source=data.source, pages=data.pages))


@router.post("/start-download")
def start_download(data: DownloadRequest, admin=Depends(require_scraper)):
    """Telegram botdan film/seriallarni yuklash (Download/Grab) jarayonini ishga tushirish."""
    if data.target not in SOURCES:
        raise HTTPException(status_code=400, detail="Noma'lum maqsadli bot")
    if data.media_type not in MEDIA_TYPES:
        raise HTTPException(status_code=400, detail="Noma'lum media turi")
    return _ensure_ok(
        ProcessManager().start_download(
            target=data.target, limit=data.limit, codes=data.codes, media_type=data.media_type
        )
    )


@router.post("/clean-duplicates")
def clean_duplicates(admin=Depends(require_scraper)):
    """Navbatdagi mavjud bazadagi dublikatlarni tekshirish va tozalash."""
    return _ensure_ok(ProcessManager().start_clean_duplicates())


@router.post("/stop")
def stop_process(admin=Depends(require_scraper)):
    """Faol ishlayotgan jarayonni xavfsiz to'xtatish."""
    return _ensure_ok(ProcessManager().stop_process())


@router.post("/clear-logs")
def clear_logs(admin=Depends(require_scraper)):
    """Konsol loglarini tozalash."""
    ProcessManager().clear_logs()
    return {"success": True, "message": "Loglar tozalandi."}


def _forbid_while_running(detail: str):
    if ProcessManager().get_status()["is_running"]:
        raise HTTPException(status_code=409, detail=detail)


@router.post("/queue/retry-all-failed")
def retry_all_failed(source: Optional[str] = Query(None), admin=Depends(require_scraper)):
    """Barcha xatolikka uchragan elementlarni qayta kutilayotgan holatga o'tkazish."""
    if source and source not in SOURCES:
        raise HTTPException(status_code=400, detail="Noto'g'ri manba")
    count = QueueManager().retry_all_failed(source=source)
    return {"success": True, "count": count, "message": f"{count} ta element qayta navbatga qo'yildi."}


@router.post("/queue/clear-by-status")
def clear_by_status(status: str = Body(..., embed=True), admin=Depends(require_scraper)):
    """Berilgan statusdagi elementlarni navbatdan o'chirish (completed, already_exists, failed...)."""
    if status not in STATUSES:
        raise HTTPException(status_code=400, detail="Noto'g'ri status")
    if status == "in_progress":
        raise HTTPException(status_code=400, detail="Jarayondagi elementlarni o'chirib bo'lmaydi")
    count = QueueManager().clear_by_status(status=status)
    return {"success": True, "count": count, "message": f"{count} ta element tozalandi."}


@router.post("/queue/{item_id}/retry")
def retry_queue_item(item_id: str, admin=Depends(require_scraper)):
    """Xatolikka uchragan elementni qayta navbatga qo'yish."""
    if not QueueManager().retry_item(item_id):
        raise HTTPException(status_code=404, detail="Element topilmadi")
    return {"success": True, "message": f"{item_id} qayta navbatga qo'yildi."}


@router.delete("/queue/{item_id}")
def delete_queue_item(item_id: str, admin=Depends(require_scraper)):
    """Elementni navbatdan o'chirish."""
    if not QueueManager().delete_item(item_id):
        raise HTTPException(status_code=404, detail="Element topilmadi")
    return {"success": True, "message": f"{item_id} o'chirildi."}
