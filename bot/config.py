from pydantic_settings import BaseSettings, SettingsConfigDict

from typing import Optional

class Settings(BaseSettings):
    BOT_TOKEN: str
    BACKEND_API_URL: str = "http://localhost:8000/api/v1"
    STORAGE_CHANNEL_ID: Optional[int] = None
    ADMIN_IDS: str = ""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
