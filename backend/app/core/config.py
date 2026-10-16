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
    PROJECT_NAME: str = "MediaPlus"
    VERSION: str = "0.1.0"
    APP_ENV: str = "development"          # development | staging | production
    DEBUG: bool = False

    # ── Database (async PostgreSQL) ──────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://kinochi:kinochi_secret@localhost:5432/kinochi"

    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if v:
            import re
            v = re.sub(r"\s+", "", str(v))
            if v.startswith("postgres://"):
                v = v.replace("postgres://", "postgresql+asyncpg://", 1)
            elif v.startswith("postgresql://"):
                v = v.replace("postgresql://", "postgresql+asyncpg://", 1)
            v = re.sub(r"([?&])sslmode=([a-zA-Z0-9_-]+)", r"\1ssl=\2", v)
            v = re.sub(r"[?&]channel_binding=[^&]+", "", v)
            v = re.sub(r"[?&]gssencmode=[^&]+", "", v)
            if "?" not in v and "&" in v:
                v = v.replace("&", "?", 1)
            v = re.sub(r"\?&", "?", v).rstrip("?&")
        return v

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
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
            ])

    # ── Security (Phase 1+) ──────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ── Telegram (Phase 4+) ──────────────────────────────────────────
    BOT_TOKEN: str
    STORAGE_CHANNEL_ID: str | int
    TELEGRAM_API_ID: int = 32571063
    TELEGRAM_API_HASH: str = "fe3038cd47d8c37788a5f4bdeef00138"
    TELEGRAM_STRING_SESSION: str = "1ApWapzMBuyF503SKFe7YvecikokTfoWvtlnlzunbRRik8mht2VtaJve7uOtwuKwQBdXkvZ_0cOn-SBVZ2jHcHJuRhdcGiVBnP_Yg0_dEVOJT6jjvVhbwepZFPTn4HkwyVqG2Z7h-HFpXRYo4HboCGLR0QCYVx8KrKVQYTK44Sxiai6atXQ7klb6tKg_Nq8S2u3x23V82J3SVM6bROoGvltvZKMZ2n9suDPUSWtg9612fCtTqsH6ohVEq-jeWUt099pWYWCBnn_yTlWiZWdhflktlGP4nD4PL52JdQDz1zUilq1B9KFsLq8DQW3jbfYzbpAzz6175F_Ve3xuD2-wsBd8--H08Is0="
    # Internal secret for bot → backend API calls (POST /users/register, etc.)
    BOT_API_SECRET: str = ""

    # ── Content Automation ───────────────────────────────────────────
    TMDB_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    AUTO_TOPIC_CHAT_ID: int | None = None
    AUTO_CONTENT_ENABLED: bool = True

    # ── TMDb Top Seed Ingestor (S2) ──────────────────────────────────
    SEED_MOVIE_TARGET: int = 1000
    SEED_TV_TARGET: int = 500
    SEED_INCLUDE_SERIES: bool = False
    SEED_MIN_VOTE_COUNT: int = 1000
    SEED_MIN_RATING: float = 7.0
    SEED_EXCLUDE_ADULT: bool = True
    SEED_BATCH_SIZE: int = 20
    SEED_NOT_FOUND_RETRY_DAYS: int = 30
    SEED_PRIORITY: int = 100
    SEED_SEARCH_DELAY_SECONDS: float = 1.0
    SEED_SEARCH_CONCURRENCY: int = 2

    model_config = {
        "env_file": (".env.local", "backend/.env.local", ".env", "backend/.env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",  # Testlar va Docker muhitida extra o'zgaruvchilar xato bermasligi uchun
    }


settings = Settings()
