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

TELEGRAM_API_ID = _parse_int(os.environ.get("TELEGRAM_API_ID"), 0)
TELEGRAM_API_HASH = (os.environ.get("TELEGRAM_API_HASH") or "").strip()
TELEGRAM_STRING_SESSION = (os.environ.get("TELEGRAM_STRING_SESSION") or "").strip()

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
STORAGE_CHANNEL_ID = _parse_chat_id(os.environ.get("STORAGE_CHANNEL_ID"), 0)
AUTO_TOPIC_CHAT_ID = _parse_chat_id(os.environ.get("AUTO_TOPIC_CHAT_ID"), 0)
BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://localhost:8000/api/v1")
BOT_API_SECRET = os.environ.get("BOT_API_SECRET", "oqqora")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Target bots
TARGET_BOTS = {
    "uzmovi": "UzmovieTV_Bot",
    "asilmedia": "asilmediabot",
    "animeelar": "Animeelar_Bot",
    "anitoob": "ANITOOBUZ_BOT",
    "kinochilar": "kinochilar_fast_bot",
}

