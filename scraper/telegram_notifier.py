import os
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)

async def notify_admin_user(user_id: int | str, message: str) -> bool:
    """Foydalanuvchiga Telegram bot orqali bildirishnoma yuboradi."""
    if not user_id:
        return False
    try:
        from app.core.config import settings
        token = settings.BOT_TOKEN
    except Exception:
        token = os.getenv("BOT_TOKEN")
    
    if not token:
        logger.warning("BOT_TOKEN topilmadi, bildirishnoma yuborilmadi.")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": int(user_id),
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(url, json=payload)
            return resp.status_code == 200
    except Exception as e:
        logger.warning(f"Telegram bildirishnoma yuborishda xatolik: {e}")
        return False


async def send_photo_to_user(user_id: int | str, photo_path: str, caption: Optional[str] = None) -> bool:
    """Foydalanuvchiga Telegram bot orqali rasm yuboradi."""
    if not user_id or not photo_path:
        return False
    try:
        from app.core.config import settings
        token = settings.BOT_TOKEN
    except Exception:
        token = os.getenv("BOT_TOKEN")

    if not token or not os.path.exists(photo_path):
        return False

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            with open(photo_path, "rb") as f:
                files = {"photo": f}
                data = {"chat_id": int(user_id), "parse_mode": "HTML"}
                if caption:
                    data["caption"] = caption
                resp = await client.post(url, data=data, files=files)
                return resp.status_code == 200
    except Exception as e:
        logger.warning(f"Telegram rasm yuborishda xatolik: {e}")
        return False
