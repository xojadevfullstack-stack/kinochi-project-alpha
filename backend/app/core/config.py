"""
Core configuration — settings loaded from environment variables.

Core Layer: framework-agnostic application settings.  Used across all
layers but depends on nothing except pydantic-settings.
"""

import os
from pydantic_settings import BaseSettings
from pydantic import field_validator, model_validator


class Settings(BaseSettings):
    """Application settings, populated from env vars / .env file."""

    # ── General ──────────────────────────────────────────────────
    PROJECT_NAME: str = "MediaPlus"
    VERSION: str = "0.1.0"
    APP_ENV: str = "development"          # development | staging | production
    ENVIRONMENT: str | None = None        # alternative env marker used by cloud platforms
    ENABLE_DEV_LOGIN: bool = False       # explicitly enable dev mock login in dev/test only
    DEBUG: bool = False

    @property
    def is_production(self) -> bool:
        """
        Fail-safe production check:
        If either APP_ENV or ENVIRONMENT is 'production', 'prod', or 'staging',
        safest side wins and evaluates to True.
        """
        prod_markers = {"production", "prod", "staging"}
        app_env_val = str(self.APP_ENV or "").strip().lower()
        env_val = str(self.ENVIRONMENT or "").strip().lower()
        return (app_env_val in prod_markers) or (env_val in prod_markers)

    # ── Database (async PostgreSQL) ──────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://kinochi:kinochi_secret@localhost:5432/kinochi"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20

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
    CORS_ORIGINS: list[str] = [
        "https://kinochi-project-alpha.vercel.app",
        "https://kinochi.uz",
    ]
    CORS_ALLOWED_ORIGINS: str = ""
    # Regex allowing legitimate Vercel deployments and preview URLs
    CORS_ORIGIN_REGEX: str | None = r"^https:\/\/(kinochi-project-alpha|kinochi-admin)(-[a-zA-Z0-9_-]+)?\.vercel\.app$"

    # ── Reverse Proxy / Rate Limiting ────────────────────────────
    TRUST_PROXY: bool = False
    TRUSTED_PROXIES_COUNT: int = 1

    def model_post_init(self, __context):
        # Guarantee core frontend domains are always present
        for core_origin in [
            "https://kinochi-project-alpha.vercel.app",
            "https://kinochi-admin.vercel.app",
            "https://kinochi.uz",
            "https://admin.kinochi.uz",
        ]:
            if core_origin not in self.CORS_ORIGINS:
                self.CORS_ORIGINS.append(core_origin)

        # Merge CORS_ALLOWED_ORIGINS alias (comma-separated or JSON list)
        if self.CORS_ALLOWED_ORIGINS:
            raw = self.CORS_ALLOWED_ORIGINS.strip()
            if raw.startswith("[") and raw.endswith("]"):
                try:
                    import json
                    parsed = json.loads(raw)
                    for o in parsed:
                        s = str(o).strip()
                        if s and s not in self.CORS_ORIGINS:
                            self.CORS_ORIGINS.append(s)
                except Exception:
                    pass
            else:
                for origin in raw.split(","):
                    o = origin.strip()
                    if o and o not in self.CORS_ORIGINS:
                        self.CORS_ORIGINS.append(o)

        if not self.is_production:
            for dev_origin in [
                "http://localhost:3000",   # website dev
                "http://localhost:3001",   # admin panel dev
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
            ]:
                if dev_origin not in self.CORS_ORIGINS:
                    self.CORS_ORIGINS.append(dev_origin)

    # ── Security (Phase 1+) ──────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    @model_validator(mode="after")
    def validate_production_security(self):
        if self.is_production:
            if not self.SECRET_KEY or self.SECRET_KEY == "change-me-in-production":
                raise ValueError("SECRET_KEY must be set to a secure secret in production!")
        return self

    # ── Telegram (Phase 4+) ──────────────────────────────────────────
    BOT_TOKEN: str
    STORAGE_CHANNEL_ID: str | int
    TELEGRAM_API_ID: int | None = None
    TELEGRAM_API_HASH: str = ""
    TELEGRAM_STRING_SESSION: str = ""

    @field_validator("TELEGRAM_API_ID", mode="before")
    @classmethod
    def validate_telegram_api_id(cls, v):
        if v is None or v == "":
            return None
        return int(v)
    # Internal secret for bot → backend API calls (POST /users/register, etc.)
    BOT_API_SECRET: str = ""
    BOT_USERNAME: str = "kinochi_mvp_bot"
    WEBSITE_URL: str = "https://kinochi-project-alpha.vercel.app"

    # ── Content Automation ───────────────────────────────────────────
    TMDB_API_KEY: str = ""
    KINOPOISK_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    AUTO_TOPIC_CHAT_ID: int | None = None
    AUTO_CONTENT_ENABLED: bool = False
    SCRAPER_ENABLED: bool = False
    UZMOVI_BOT_CODE_VERIFIED: bool = False
    AUTO_INDEX_DRY_RUN: bool = True
    AUTO_INDEX_ALLOWED_CHAT_IDS: list[int] = []
    MOVIE_RUNTIME_TOLERANCE_MINUTES: int = 30
    MOVIE_RUNTIME_TOLERANCE_PERCENT: int = 15

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
        "env_file": None if os.environ.get("APP_ENV") == "testing" else (".env.local", "backend/.env.local", ".env", "backend/.env"),
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore",  # Testlar va Docker muhitida extra o'zgaruvchilar xato bermasligi uchun
    }


settings = Settings()
