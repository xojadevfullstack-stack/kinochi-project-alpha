import os
import sys
import logging
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, Body
from pydantic import BaseModel, Field

from dataclasses import asdict
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db_session
from app.infrastructure.db.models.movie import MovieModel
from app.core.cache import delete_cache_pattern

logger = logging.getLogger(__name__)

# The scraper lives next to backend/ (project root). In the production Docker image
# only backend/ is copied, so the import must be optional: the rest of the API
# must keep working and these endpoints answer 503 with a clear message.
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

try:
    from scraper.queue_manager import QueueManager, QueueItem
    from scraper.process_manager import ProcessManager
    from scraper.state_manager import StateManager
    SCRAPER_AVAILABLE = True
except Exception as _exc:  # pragma: no cover
    QueueManager = None  # type: ignore
    ProcessManager = None  # type: ignore
    StateManager = None  # type: ignore
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

SOURCES = ("uzmovi", "asilmedia", "anitoob", "animeelar", "all")
MEDIA_TYPES = ("all", "movie", "series")
STATUSES = ("pending", "in_progress", "completed", "failed", "already_exists", "needs_review")


class ParseRequest(BaseModel):
    source: str = Field("uzmovi", description="Manba: uzmovi, asilmedia, anitoob yoki animeelar")
    pages: int = Field(3, ge=1, le=50, description="Sahifalar soni")
    start_page: Optional[int] = Field(None, ge=1, description="Boshlang'ich sahifa (bo'sh qolsa state.json dan)")
    min_rating: Optional[float] = Field(None, ge=0.0, le=10.0, description="Minimal reyting (default 6.0)")


class DownloadRequest(BaseModel):
    target: str = Field("uzmovi", description="Maqsadli bot: uzmovi, asilmedia, anitoob yoki animeelar")
    limit: int = Field(5, ge=1, le=500, description="Yuklanadigan kinolar soni")
    codes: Optional[str] = Field(None, max_length=500, description="Muayyan film kodlari (masalan: 15 yoki 1-5 yoki 10,15)")
    media_type: str = Field("all", description="all, movie yoki series")


class AutopilotRequest(BaseModel):
    source: str = Field("all", description="Manba: uzmovi, asilmedia, anitoob, animeelar yoki all")
    pages: Optional[int] = Field(None, ge=1, le=50, description="Sahifalar soni (ixtiyoriy, avtonom rejimda kerak emas)")
    limit: Optional[int] = Field(None, ge=1, le=500, description="Yuklanadigan kinolar limiti (ixtiyoriy)")
    media_type: str = Field("all", description="all, movie yoki series")
    min_rating: Optional[float] = Field(6.0, ge=0.0, le=10.0, description="Minimal reyting filtri")


class UpdateStateRequest(BaseModel):
    uzmovi_current_page: Optional[int] = None
    uzmovi_total_pages: Optional[int] = None
    asilmedia_current_page: Optional[int] = None
    asilmedia_total_pages: Optional[int] = None
    anitoob_current_page: Optional[int] = None
    anitoob_total_pages: Optional[int] = None
    animeelar_current_page: Optional[int] = None
    animeelar_total_pages: Optional[int] = None
    min_rating: Optional[float] = None


class StatusResponse(BaseModel):
    is_running: bool
    task_type: str
    current_action: str
    current_item: Optional[Dict[str, Any]] = None
    progress: Dict[str, Any]
    started_at: Optional[str] = None
    elapsed_seconds: int = 0
    speed_movies_per_min: float = 0.0
    bot_status: str = "idle"
    logs: List[Dict[str, Any]]
    stats: Dict[str, int]
    state: Optional[Dict[str, Any]] = None


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


@router.get("/state")
def get_scraper_state(admin=Depends(require_scraper)):
    """Scraper sahifa xotirasi (checkpoint) va parametrlarini olish."""
    return StateManager().get_state()


@router.post("/state")
def update_scraper_state(data: UpdateStateRequest, admin=Depends(require_scraper)):
    """Scraper sahifa xotirasi yoki parametrlarini yangilash."""
    payload = {k: v for k, v in data.dict().items() if v is not None}
    return StateManager().update(**payload)


@router.post("/autopilot")
def start_autopilot(data: AutopilotRequest, admin=Depends(require_scraper)):
    """Bitta tugma bilan to'liq avtonom sikl (Parse + 6+ Filtr + Download) ni boshlash."""
    return _ensure_ok(
        ProcessManager().start_autopilot(
            source=data.source,
            pages=data.pages,
            limit=data.limit,
            media_type=data.media_type,
            min_rating=data.min_rating
        )
    )


@router.post("/retry-failed")
def retry_failed(admin=Depends(require_scraper)):
    """Barcha xatolik bergan filmlarni qayta navbatga qo'yish."""
    return _ensure_ok(ProcessManager().start_retry_failed())


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
    return _ensure_ok(
        ProcessManager().start_parse(
            source=data.source,
            pages=data.pages,
            start_page=data.start_page,
            min_rating=data.min_rating
        )
    )


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


@router.get("/search-site")
async def search_site(
    q: str = Query(..., min_length=2, max_length=200, description="Qidiruv so'rovi"),
    source: str = Query("all", description="all, uzmovi, asilmedia yoki animeelar"),
    admin=Depends(require_scraper),
):
    """Uzmovi, Asilmedia va Animeelar sayt/botlaridan film/seriallarni qidirish."""
    from scraper.site_search import search_sites
    results = await search_sites(query=q, source=source)
    return {"results": results, "count": len(results)}


@router.post("/queue-add")
def queue_add(
    item_data: Dict[str, Any] = Body(...),
    admin=Depends(require_scraper),
):
    """Qidiruv natijalaridan elementni navbatga qo'shish."""
    qm = QueueManager()
    is_dup = item_data.get("is_duplicate", False)
    new_item = QueueItem(
        id=item_data["id"],
        source=item_data["source"],
        title=item_data["title"],
        year=item_data.get("year"),
        media_type=item_data.get("media_type", "movie"),
        url=item_data.get("url", ""),
        poster_url=item_data.get("poster_url"),
        status="already_exists" if is_dup else "pending",
        error_message=f"Bazada mavjud: {item_data.get('db_title')}" if is_dup else None,
    )
    qm.add_item(new_item)
    return {"success": True, "message": f"'{new_item.title}' navbatga qo'shildi.", "item": new_item.__dict__}


@router.post("/quick-grab")
def quick_grab(
    item_data: Dict[str, Any] = Body(...),
    admin=Depends(require_scraper),
):
    """Qidiruv natijalaridagi filmni darhol Telegram botdan yuklashni boshlash."""
    qm = QueueManager()
    new_item = QueueItem(
        id=item_data["id"],
        source=item_data["source"],
        title=item_data["title"],
        year=item_data.get("year"),
        media_type=item_data.get("media_type", "movie"),
        url=item_data.get("url", ""),
        poster_url=item_data.get("poster_url"),
        status="pending",
    )
    qm.add_item(new_item)

    target_bot = item_data["source"]
    res = ProcessManager().start_download(
        target=target_bot,
        limit=1,
        codes=None,
        media_type=item_data.get("media_type", "movie"),
        item_id=new_item.id,
    )
    return _ensure_ok(res)


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


@router.post("/queue/{item_id}/grab-now")
def grab_now(item_id: str, admin=Depends(require_scraper)):
    """Aynan bitta film yoki serialni navbatdan darhol yuklashni boshlash."""
    qm = QueueManager()
    item = qm.items.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Element navbatda topilmadi")

    return _ensure_ok(
        ProcessManager().start_download(
            target=item.source,
            limit=1,
            item_id=item.id,
            media_type=item.media_type
        )
    )


class UpdateQueueItemRequest(BaseModel):
    title: str = Field(..., min_length=2)
    year: Optional[int] = None
    poster_url: Optional[str] = None
    original_title: Optional[str] = None
    media_type: Optional[str] = "movie"
    status: Optional[str] = "pending"


class FixDbMovieRequest(BaseModel):
    title: str = Field(..., min_length=2)
    original_title: Optional[str] = None
    release_year: Optional[int] = None
    description: Optional[str] = None
    poster_url: Optional[str] = None
    trailer_url: Optional[str] = None
    genres: Optional[str] = None
    imdb_rating: Optional[float] = None
    tmdb_id: Optional[int] = None


@router.get("/incomplete-movies")
async def get_incomplete_movies(
    db: AsyncSession = Depends(get_db_session),
    admin=Depends(require_scraper),
):
    """Bazada yoki navbatda nomi/tavsifi to'liq bo'lmagan, moderatsiya talab qiluvchi kinolar."""
    # 1. DB items
    res = await db.execute(
        select(MovieModel)
        .where(
            (func.lower(MovieModel.title).in_(["kino", "film", "serial", "tarjima kino", "premyera", "noma'lum"]))
            | (func.length(MovieModel.title) < 4)
            | (MovieModel.description == None)
            | (func.length(MovieModel.description) < 20)
        )
        .order_by(MovieModel.id.desc())
        .limit(50)
    )
    db_movies = res.scalars().all()

    # 2. Queue items
    qm = QueueManager()
    queue_items = []
    suspicious_words = {"kino", "film", "serial", "tarjima kino", "premyera", "noma'lum", "movie"}
    for item in qm.items.values():
        if (
            item.status == "needs_review"
            or item.title.lower().strip() in suspicious_words
            or len(item.title.strip()) < 4
        ):
            queue_items.append(item)

    return {
        "db_movies": [
            {
                "id": m.id,
                "code": m.code,
                "title": m.title,
                "original_title": m.original_title,
                "release_year": m.release_year,
                "description": m.description,
                "poster_url": m.poster_url,
                "genres": m.genres,
                "imdb_rating": m.imdb_rating,
                "tmdb_id": m.tmdb_id,
            }
            for m in db_movies
        ],
        "queue_items": [asdict(it) for it in queue_items],
    }


@router.put("/queue/{item_id}")
def update_queue_item(
    item_id: str,
    req: UpdateQueueItemRequest,
    admin=Depends(require_scraper),
):
    """Navbatdagi element ma'lumotlarini (nomi, yili, posteri) qo'lda to'g'rilash va tayyorlash."""
    qm = QueueManager()
    success = qm.update_item_details(
        item_id=item_id,
        title=req.title,
        year=req.year,
        poster_url=req.poster_url,
        original_title=req.original_title,
        media_type=req.media_type or "movie",
        status=req.status or "pending",
        error_message=None,
    )
    if not success:
        raise HTTPException(status_code=404, detail="Element topilmadi")
    return {"success": True, "message": f"{item_id} muvaffaqiyatli yangilandi va navbatga qo'yildi."}


@router.post("/db-movies/{movie_id}/fix")
async def fix_db_movie(
    movie_id: int,
    req: FixDbMovieRequest,
    db: AsyncSession = Depends(get_db_session),
    admin=Depends(require_scraper),
):
    """Bazada chala bo'lib qolgan kinoni (masalan 'Kino') qo'lda yoki TMDb orqali to'g'rilash."""
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Film bazada topilmadi")

    movie.title = req.title
    if req.original_title is not None:
        movie.original_title = req.original_title
    if req.release_year is not None:
        movie.release_year = req.release_year
    if req.description is not None:
        movie.description = req.description
    if req.poster_url is not None:
        movie.poster_url = req.poster_url
    if req.trailer_url is not None:
        movie.trailer_url = req.trailer_url
    if req.genres is not None:
        movie.genres = req.genres
    if req.imdb_rating is not None:
        movie.imdb_rating = req.imdb_rating
    if req.tmdb_id is not None:
        movie.tmdb_id = req.tmdb_id

    await db.commit()
    await db.refresh(movie)
    await delete_cache_pattern("*")
    return {"success": True, "message": f"'{movie.title}' (ID: {movie_id}) muvaffaqiyatli yangilandi!"}


@router.delete("/db-movies/{movie_id}")
async def delete_db_movie(
    movie_id: int,
    db: AsyncSession = Depends(get_db_session),
    admin=Depends(require_scraper),
):
    """Bazada yaroqsiz bo'lib qolgan kinoni butunlay o'chirish."""
    movie = await db.get(MovieModel, movie_id)
    if not movie:
        raise HTTPException(status_code=404, detail="Film bazada topilmadi")
    await db.delete(movie)
    await db.commit()
    await delete_cache_pattern("*")
    return {"success": True, "message": f"Film #{movie_id} bazadan o'chirildi."}

