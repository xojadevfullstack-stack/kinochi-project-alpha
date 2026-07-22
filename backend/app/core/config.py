"""
Core configuration — settings loaded from environment variables.

Core Layer: framework-agnostic application settings.  Used across all
layers but depends on nothing except pydantic-settings.
"""

from pydantic_settings import BaseSettings
from pydantic import field_validator


class Settings(BaseSettings):
    """Application settings, populated from env vars / .env file."""

    # ── General ──────────────────────────────────────────────────
    PROJECT_NAME: str = "Kinochi"
    VERSION: str = "0.1.0"
    APP_ENV: str = "development"          # development | staging | production
    DEBUG: bool = False

    # ── Database (async PostgreSQL) ──────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://kinochi:kinochi_secret@localhost:5432/kinochi"

    # ── Redis ────────────────────────────────────────────────────
    REDIS_URL: str = "redis://localhost:6379/0"

    @field_validator("REDIS_URL", mode="before")
    @classmethod
    def validate_redis_url(cls, v: str) -> str:
        if v:
            v = v.replace("https://", "").replace("http://", "")
            if not v.startswith(("redis://", "rediss://", "unix://")):
                v = f"redis://{v}"
            if "upstash.io" in v and v.startswith("redis://"):
                v = v.replace("redis://", "rediss://", 1)
        return v

    # ── CORS ─────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = []

    def model_post_init(self, __context):
        if self.APP_ENV != "production":
            self.CORS_ORIGINS.extend([
                "http://localhost:3000",   # website dev
                "http://localhost:3001",   # admin panel dev
            ])

    # ── Security (Phase 1+) ──────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Telegram (Phase 4+) ──────────────────────────────────────────
    BOT_TOKEN: str
    STORAGE_CHANNEL_ID: str | int
    TELEGRAM_API_ID: int
    TELEGRAM_API_HASH: str
    # Internal secret for bot → backend API calls (POST /users/register, etc.)
    BOT_API_SECRET: str = ""

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",  # Testlar va Docker muhitida extra o'zgaruvchilar xato bermasligi uchun
    }


settings = Settings()
