import os
from dotenv import load_dotenv

# Load env files
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, "bot", ".env"))

TELEGRAM_API_ID = int(os.environ.get("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.environ.get("TELEGRAM_API_HASH", "")

BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
STORAGE_CHANNEL_ID = int(os.environ.get("STORAGE_CHANNEL_ID", "0"))
AUTO_TOPIC_CHAT_ID = int(os.environ.get("AUTO_TOPIC_CHAT_ID", "0"))
BACKEND_API_URL = os.environ.get("BACKEND_API_URL", "http://localhost:8000/api/v1")
BOT_API_SECRET = os.environ.get("BOT_API_SECRET", "oqqora")
DATABASE_URL = os.environ.get("DATABASE_URL", "")

# Target bots
TARGET_BOTS = {
    "uzmovi": "UzmovieTV_Bot",
    "asilmedia": "asilmediabot"
}

