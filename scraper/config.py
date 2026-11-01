import os
from dotenv import load_dotenv

# Load env files
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for env_path in [
    os.path.join(BASE_DIR, ".env.local"),
    os.path.join(BASE_DIR, "backend", ".env.local"),
    os.path.join(os.getcwd(), ".env.local"),
    os.path.join(os.getcwd(), "backend", ".env.local"),
    os.path.join(BASE_DIR, "backend", ".env"),
    os.path.join(BASE_DIR, "bot", ".env"),
    os.path.join(BASE_DIR, ".env"),
    os.path.join(os.getcwd(), ".env"),
    os.path.join(os.getcwd(), "backend", ".env"),
]:
    if os.path.exists(env_path):
        load_dotenv(env_path)

def _parse_int(val, default: int = 0) -> int:
    try:
        if val is None:
            return default
        parsed = int(str(val).strip())
        return parsed if parsed != 0 else default
    except (ValueError, TypeError):
        return default

def _parse_chat_id(val, default: int = 0):
    if val is None:
        return default
    val_str = str(val).strip()
    if not val_str or val_str == "0":
        return default
    try:
        return int(val_str)
    except (ValueError, TypeError):
        return val_str

def _parse_bool(val, default: bool = False) -> bool:
    if val is None:
        return default
    if isinstance(val, bool):
        return val
    return str(val).strip().lower() in ("1", "true", "yes", "on")


def is_uzmovi_bot_code_verified() -> bool:
    try:
        from app.core.config import settings as _backend_settings
        if "UZMOVI_BOT_CODE_VERIFIED" in os.environ:
            return _parse_bool(os.environ.get("UZMOVI_BOT_CODE_VERIFIED"), False)
        return bool(getattr(_backend_settings, "UZMOVI_BOT_CODE_VERIFIED", False))
    except Exception:
        return _parse_bool(os.environ.get("UZMOVI_BOT_CODE_VERIFIED"), False)


def is_scraper_enabled() -> bool:
    try:
        from app.core.config import settings as _backend_settings
        if "SCRAPER_ENABLED" in os.environ:
            return _parse_bool(os.environ.get("SCRAPER_ENABLED"), False)
        return bool(getattr(_backend_settings, "SCRAPER_ENABLED", False))
    except Exception:
        return _parse_bool(os.environ.get("SCRAPER_ENABLED"), False)


TELEGRAM_API_ID = _parse_int(os.environ.get("TELEGRAM_API_ID"), 0)
TELEGRAM_API_HASH = (os.environ.get("TELEGRAM_API_HASH") or "").strip()
TELEGRAM_STRING_SESSION = (os.environ.get("TELEGRAM_STRING_SESSION") or "").strip()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
STORAGE_CHANNEL_ID = _parse_chat_id(os.environ.get("STORAGE_CHANNEL_ID"), 0)
AUTO_TOPIC_CHAT_ID = _parse_chat_id(os.environ.get("AUTO_TOPIC_CHAT_ID"), 0)
BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://localhost:8000/api/v1")
BOT_API_SECRET = os.environ.get("BOT_API_SECRET", "oqqora")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
UZMOVI_BOT_CODE_VERIFIED = _parse_bool(os.environ.get("UZMOVI_BOT_CODE_VERIFIED"), False)
SCRAPER_ENABLED = _parse_bool(os.environ.get("SCRAPER_ENABLED"), False)

# Target bots
TARGET_BOTS = {
    "uzmovi": "UzmovieTV_Bot",
    "asilmedia": "asilmediabot",
    "animeelar": "Animeelar_Bot",
    "anitoob": "ANITOOBUZ_BOT",
    "kinochilar": "kinochilar_fast_bot",
}

