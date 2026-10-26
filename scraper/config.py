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

DEFAULT_TELEGRAM_API_ID = 32571063
DEFAULT_TELEGRAM_API_HASH = "fe3038cd47d8c37788a5f4bdeef00138"
DEFAULT_TELEGRAM_STRING_SESSION = (
    "1ApWapzMBuyF503SKFe7YvecikokTfoWvtlnlzunbRRik8mht2VtaJve7uOtwuKwQBdXkvZ_0cOn-SBVZ2jHcHJuRhdcGiVBnP_Yg0_dEVOJT6jjvVhbwepZFPTn4HkwyVqG2Z7h-HFpXRYo4HboCGLR0QCYVx8KrKVQYTK44Sxiai6atXQ7klb6tKg_Nq8S2u3x23V82J3SVM6bROoGvltvZKMZ2n9suDPUSWtg9612fCtTqsH6ohVEq-jeWUt099pWYWCBnn_yTlWiZWdhflktlGP4nD4PL52JdQDz1zUilq1B9KFsLq8DQW3jbfYzbpAzz6175F_Ve3xuD2-wsBd8--H08Is0="
)

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

TELEGRAM_API_ID = _parse_int(os.environ.get("TELEGRAM_API_ID"), DEFAULT_TELEGRAM_API_ID)
if not TELEGRAM_API_ID:
    TELEGRAM_API_ID = DEFAULT_TELEGRAM_API_ID

TELEGRAM_API_HASH = (os.environ.get("TELEGRAM_API_HASH") or "").strip() or DEFAULT_TELEGRAM_API_HASH
TELEGRAM_STRING_SESSION = (os.environ.get("TELEGRAM_STRING_SESSION") or "").strip() or DEFAULT_TELEGRAM_STRING_SESSION

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

