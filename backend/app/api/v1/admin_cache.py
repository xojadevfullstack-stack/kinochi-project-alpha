import logging
from fastapi import APIRouter, Depends, status
from app.api.deps import get_current_admin
from app.core.cache import flush_all_cache

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/cache", tags=["admin-cache"])


@router.post("/flush", status_code=status.HTTP_200_OK)
async def flush_cache_endpoint(admin: dict = Depends(get_current_admin)):
    """
    Admin-only endpoint: In-memory zaxira keshini va Redis keshini bir vaqtda to'liq tozalaydi.
    """
    admin_id = admin.id if hasattr(admin, "id") else admin.get("id")
    logger.info(f"Admin (ID: {admin_id}) keshni to'liq tozalash (flush) so'rovini yubordi.")
    await flush_all_cache()
    return {
        "status": "success",
        "message": "In-memory va Redis keshlari muvaffaqiyatli tozalandi.",
    }
