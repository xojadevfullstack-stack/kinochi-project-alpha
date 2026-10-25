import os
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Union

BOT_DIR = os.path.dirname(os.path.abspath(__file__))

class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    BACKEND_API_URL: str = "http://127.0.0.1:8000/api/v1"
    STORAGE_CHANNEL_ID: Union[int, str, None] = None
    AUTO_TOPIC_CHAT_ID: Union[int, str, None] = None
    # Must match BOT_API_SECRET in backend/.env
    BOT_API_SECRET: str = ""
    WEBSITE_URL: str = "https://kinochi-project-alpha.vercel.app"
    BOT_USERNAME: str = "kinochi_mvp_bot"

    # Incident fix flags
    AUTO_CONTENT_ENABLED: bool = False
    AUTO_INDEX_DRY_RUN: bool = False
    AUTO_INDEX_ALLOWED_CHAT_IDS: list[int] = []
    BOT_DROP_PENDING_UPDATES: bool = False
    MOVIE_RUNTIME_TOLERANCE_MINUTES: int = 30
    MOVIE_RUNTIME_TOLERANCE_PERCENT: int = 15
    AUTO_INDEX_DEBOUNCE_SECONDS: float = 2.0
    AUTO_INDEX_COPY_DELAY_SECONDS: float = 1.0

    @field_validator("AUTO_INDEX_ALLOWED_CHAT_IDS", mode="before")
    @classmethod
    def validate_allowed_chat_ids(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return []
            return [int(x.strip()) for x in v.split(",") if x.strip()]
        if isinstance(v, (list, tuple, set)):
            return [int(x) for x in v]
        return []

    model_config = SettingsConfigDict(
        env_file=os.path.join(BOT_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
