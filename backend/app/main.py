"""
Kinochi Backend — FastAPI application entrypoint.

Presentation Layer: This is the top-level composition root that wires
together all routers, middleware, and lifecycle hooks.  No business
logic lives here.
"""

import logging
logging.info("CHECKPOINT 5: main.py moduli import qilinmoqda")

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.api.v1 import movies, categories, users, channels, auth, broadcasts, series, sources, pages
from app.api.limiter import limiter

# ── Lifespan (startup / shutdown hooks) ──────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle manager."""
    import asyncio
    import os
    import httpx
    import logging

    logging.info("CHECKPOINT 6: lifespan/startup handler boshlandi")

    async def keep_alive():
        url = os.getenv("RENDER_EXTERNAL_URL")
        if not url:
            return
        ping_url = f"{url}/health"
        while True:
            await asyncio.sleep(14 * 60)
            try:
                async with httpx.AsyncClient() as client:
                    await client.get(ping_url)
            except Exception as e:
                logging.error(f"Backend keep-alive failed: {e}")

    async def init_redis_bg():
        from app.core.job_manager import job_manager
        logging.info("Redis'ga ulanmoqda...")
        try:
            # Test connection
            await job_manager._redis.ping()
            logging.info("Redis ulandi.")
        except Exception as e:
            logging.error(f"Redis ulanmadi: {e}. Fon vazifalar vaqtincha ishlamaydi.")

    logging.info("CHECKPOINT 7: orqa fon vazifalari (keep_alive) ishga tushirilmoqda")
    task = asyncio.create_task(keep_alive())
    logging.info("CHECKPOINT 8: orqa fon vazifalari (redis) ishga tushirilmoqda")
    redis_task = asyncio.create_task(init_redis_bg())
    
    logging.info("CHECKPOINT 8b: DB dan test so'rov yuborilmoqda (engine ping)")
    try:
        from app.infrastructure.db.session import engine
        from sqlalchemy import text
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        logging.info("CHECKPOINT 8c: DB test so'rovi tugadi (ulandi)")
    except Exception as db_err:
        logging.error(f"DB test xatosi: {db_err}")
    
    logging.info("CHECKPOINT 9: FastAPI lifespan yield qildi (server tayyor)")
    yield
    logging.info("CHECKPOINT 9z: FastAPI lifespan shutdown boshlandi")
    task.cancel()
    redis_task.cancel()


# ── App factory ──────────────────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# ── Routers ──────────────────────────────────────────────────────
app.include_router(movies.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(channels.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(broadcasts.router, prefix="/api/v1")
app.include_router(series.router, prefix="/api/v1")
app.include_router(pages.router, prefix="/api/v1")
app.include_router(sources.router, prefix="/api/v1/sources", tags=["sources"])

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Bot-Secret"],
)


# ── Health-check endpoint ────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """
    Basic liveness probe.
    Returns 200 if the process is running.
    Future phases will add readiness checks for DB / Redis.
    """
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }
