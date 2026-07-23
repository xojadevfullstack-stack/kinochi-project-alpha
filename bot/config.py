from pydantic_settings import BaseSettings, SettingsConfigDict

from typing import Optional, Union

class Settings(BaseSettings):
    BOT_TOKEN: str
    BACKEND_API_URL: str = "http://localhost:8000/api/v1"
    STORAGE_CHANNEL_ID: Union[int, str, None] = None
    # Must match BOT_API_SECRET in backend/.env
    BOT_API_SECRET: str = ""
    WEBSITE_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
