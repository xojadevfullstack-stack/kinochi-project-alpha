import os
import sys
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field

# Ensure root dir is in sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.api.deps import get_current_admin
from scraper.queue_manager import QueueManager
from scraper.process_manager import ProcessManager

router = APIRouter(prefix="/scraper", tags=["scraper"])

class ParseRequest(BaseModel):
    source: str = Field("uzmovi", description="Manba: uzmovi yoki asilmedia")
    pages: int = Field(3, ge=1, le=20, description="Sahifalar soni")

class DownloadRequest(BaseModel):
    target: str = Field("uzmovi", description="Maqsadli bot: uzmovi yoki asilmedia")
    limit: int = Field(5, ge=1, le=100, description="Yuklanadigan kinolar soni")
    codes: Optional[str] = Field(None, description="Muayyan film kodlari (masalan: 15 yoki 1-5 yoki 10,15)")
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

@router.get("/status", response_model=StatusResponse)
async def get_status(admin=Depends(get_current_admin)):
    """Scraper jarayonining hozirgi holati, progressi va loglarini olish."""
    pm = ProcessManager()
    return pm.get_status()

@router.get("/queue")
async def get_queue(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query("all"),
    source: Optional[str] = Query("all"),
    search: Optional[str] = Query(None),
    admin=Depends(get_current_admin)
):
    """Scraper navbatidagi filmlar va seriallar ro'yxatini olish."""
    qm = QueueManager()
    skip = (page - 1) * page_size
    items, total_count = qm.get_filtered(
        status=status,
        source=source,
        search=search,
        skip=skip,
        limit=page_size
    )
    total_pages = (total_count + page_size - 1) // page_size if total_count > 0 else 1

    return {
        "items": [item.__dict__ for item in items],
        "total": total_count,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
        "stats": qm.stats()
    }

@router.post("/start-parse")
async def start_parse(
    data: ParseRequest,
    admin=Depends(get_current_admin)
):
    """Saytdan katalog yig'ish (Parse) jarayonini ishga tushirish."""
    pm = ProcessManager()
    res = pm.start_parse(source=data.source, pages=data.pages)
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@router.post("/start-download")
async def start_download(
    data: DownloadRequest,
    admin=Depends(get_current_admin)
):
    """Telegram botdan film/seriallarni yuklash (Download/Grab) jarayonini ishga tushirish."""
    pm = ProcessManager()
    res = pm.start_download(
        target=data.target,
        limit=data.limit,
        codes=data.codes,
        media_type=data.media_type
    )
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@router.post("/clean-duplicates")
async def clean_duplicates(admin=Depends(get_current_admin)):
    """Navbatdagi mavjud bazadagi dublikatlarni tekshirish va tozalash."""
    pm = ProcessManager()
    res = pm.start_clean_duplicates()
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@router.post("/stop")
async def stop_process(admin=Depends(get_current_admin)):
    """Faol ishlayotgan jarayonni xavfsiz to'xtatish."""
    pm = ProcessManager()
    res = pm.stop_process()
    if not res.get("success"):
        raise HTTPException(status_code=400, detail=res.get("message"))
    return res

@router.post("/clear-logs")
async def clear_logs(admin=Depends(get_current_admin)):
    """Konsol loglarini tozalash."""
    pm = ProcessManager()
    pm.clear_logs()
    return {"success": True, "message": "Loglar tozalandi."}

@router.post("/queue/{item_id}/retry")
async def retry_queue_item(item_id: str, admin=Depends(get_current_admin)):
    """Xatolikka uchragan elementni qayta navbatga qo'yish."""
    qm = QueueManager()
    success = qm.retry_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Element topilmadi")
    return {"success": True, "message": f"{item_id} qayta navbatga qo'yildi."}

@router.delete("/queue/{item_id}")
async def delete_queue_item(item_id: str, admin=Depends(get_current_admin)):
    """Elementni navbatdan o'chirish."""
    qm = QueueManager()
    success = qm.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Element topilmadi")
    return {"success": True, "message": f"{item_id} o'chirildi."}

@router.post("/queue/retry-all-failed")
async def retry_all_failed(
    source: Optional[str] = Query(None),
    admin=Depends(get_current_admin)
):
    """Barcha xatolikka uchragan elementlarni qayta kutilayotgan holatga o'tkazish."""
    qm = QueueManager()
    count = qm.retry_all_failed(source=source)
    return {"success": True, "count": count, "message": f"{count} ta element qayta navbatga qo'yildi."}

@router.post("/queue/clear-by-status")
async def clear_by_status(
    status: str = Body(..., embed=True),
    admin=Depends(get_current_admin)
):
    """Berilgan statusdagi barcha elementlarni navbatdan o'chirish (masalan completed, already_exists)."""
    qm = QueueManager()
    count = qm.clear_by_status(status=status)
    return {"success": True, "count": count, "message": f"{count} ta {status} element tozalandi."}
