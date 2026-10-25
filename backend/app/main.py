"""
Kinochi Backend — FastAPI application entrypoint.

Presentation Layer: This is the top-level composition root that wires
together all routers, middleware, and lifecycle hooks.  No business
logic lives here.
"""

import re
import logging
logging.info("CHECKPOINT 5: main.py moduli import qilinmoqda")

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.api.v1 import movies, categories, users, channels, auth, broadcasts, series, sources, pages, telegram_auth, reviews, statistics, content_lookup, scraper, collections, search, reports, audit, blacklist, series_subscriptions, rejected, admin_cache
from app.api.limiter import limiter
from fastapi.staticfiles import StaticFiles
import os

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
        from app.core.config import settings
        redis_url = getattr(settings, "REDIS_URL", "")
        if "SIZNING_UPSTASH_PAROLINGIZ" in redis_url or "parol" in redis_url.lower():
            logging.info("Redis: Placeholder URL aniqlandi, fon ulanish o'tkazib yuborildi.")
            return
        from app.core.job_manager import job_manager
        logging.info("Redis'ga ulanmoqda...")
        try:
            # Test connection
            await job_manager._redis.ping()
            logging.info("Redis ulandi.")
        except Exception as e:
            logging.error(f"Redis ulanmadi: {e}. Fon vazifalar vaqtincha ishlamaydi.")

    async def db_keep_warm():
        """Neon PostgreSQL auto-suspend (uyqu) rejimiga ketib qolmasligi uchun har 3.5 daqiqada ping."""
        from app.infrastructure.db.session import engine
        from sqlalchemy import text
        while True:
            await asyncio.sleep(210)
            try:
                async with engine.begin() as conn:
                    await conn.execute(text("SELECT 1"))
            except Exception as e:
                logging.debug(f"DB keep-warm ping: {e}")

    logging.info("CHECKPOINT 7: orqa fon vazifalari (keep_alive) ishga tushirilmoqda")
    task = asyncio.create_task(keep_alive())
    logging.info("CHECKPOINT 8: orqa fon vazifalari (redis, db_warm) ishga tushirilmoqda")
    redis_task = asyncio.create_task(init_redis_bg())
    db_warm_task = asyncio.create_task(db_keep_warm())
    
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
    db_warm_task.cancel()


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

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled server error on {request.method} {request.url.path}: {exc}", exc_info=True)
    headers = {}
    origin = request.headers.get("origin")
    if origin:
        is_allowed = False
        if origin in settings.CORS_ORIGINS:
            is_allowed = True
        elif re.match(r"^https://.*\.vercel\.app$", origin):
            is_allowed = True

        if is_allowed:
            headers["Access-Control-Allow-Origin"] = origin
            headers["Access-Control-Allow-Credentials"] = "true"
            headers["Access-Control-Allow-Headers"] = "*"
            headers["Access-Control-Allow-Methods"] = "*"

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Serverda kutilmagan xatolik yuz berdi. Bir ozdan so'ng qayta urinib ko'ring.",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
        },
        headers=headers,
    )

app.add_middleware(SlowAPIMiddleware)

@app.get("/api/v1/diag")
async def diag():
    import traceback
    from app.infrastructure.db.session import async_session_factory
    from sqlalchemy import text
    db_status = "unknown"
    err = None
    count = -1
    try:
        async with async_session_factory() as session:
            res = await session.execute(text("SELECT count(*) FROM movies"))
            count = res.scalar()
            db_status = "connected"
    except Exception as e:
        db_status = "error"
        err = f"{type(e).__name__}: {str(e)}"
    
    return {
        "version": settings.VERSION,
        "commit": "diag-v1",
        "db_status": db_status,
        "movies_count": count,
        "db_error": err,
        "database_url_masked": settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "not_set",
    }


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
app.include_router(telegram_auth.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(statistics.router, prefix="/api/v1")
app.include_router(content_lookup.router, prefix="/api/v1")
app.include_router(scraper.router, prefix="/api/v1")
app.include_router(collections.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")
app.include_router(audit.router, prefix="/api/v1")
app.include_router(blacklist.router, prefix="/api/v1")
app.include_router(series_subscriptions.router, prefix="/api/v1")
app.include_router(rejected.router, prefix="/api/v1")
app.include_router(admin_cache.router, prefix="/api/v1")

# ── Static Uploads ───────────────────────────────────────────────
os.makedirs("uploads/reports", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Root endpoint ────────────────────────────────────────────────
@app.get("/", tags=["root"])
async def root():
    """Root endpoint returning 200 for health checks."""
    return {"status": "ok", "service": "kinochi-backend", "docs": "/docs"}


# ── Health-check endpoint ────────────────────────────────────────
@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """
    Basic liveness probe.
    Returns 200 if the process is running.
    Includes bot_alive status.
    """
    from app.core.bot_status import is_bot_alive
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "bot_alive": is_bot_alive(),
    }
