import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, Union

BOT_DIR = os.path.dirname(os.path.abspath(__file__))

class Settings(BaseSettings):
    BOT_TOKEN: str = ""
    BACKEND_API_URL: str = "http://127.0.0.1:8000/api/v1"
    STORAGE_CHANNEL_ID: Union[int, str, None] = None
    # Must match BOT_API_SECRET in backend/.env
    BOT_API_SECRET: str = ""
    WEBSITE_URL: str = "https://kinochi-project-alpha.vercel.app"

    model_config = SettingsConfigDict(
        env_file=os.path.join(BOT_DIR, ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
