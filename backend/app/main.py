"""
Kinochi Backend — FastAPI application entrypoint.

Presentation Layer: This is the top-level composition root that wires
together all routers, middleware, and lifecycle hooks.  No business
logic lives here.
"""

import re
import uuid
import logging
logging.info("CHECKPOINT 5: main.py moduli import qilinmoqda")

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request, Depends, Response, status
from fastapi.responses import RedirectResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.api.deps import get_current_admin
from app.api.v1 import movies, categories, users, channels, auth, broadcasts, series, sources, pages, telegram_auth, reviews, statistics, content_lookup, scraper, collections, search, reports, audit, blacklist, series_subscriptions, rejected, admin_cache, content_requests, actors
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

    # Guard: Non-production connected to remote/external database warning
    if not settings.is_production:
        from urllib.parse import urlparse
        try:
            clean_db = str(settings.DATABASE_URL).replace("postgresql+asyncpg://", "http://").replace("postgres://", "http://")
            parsed_db = urlparse(clean_db)
            db_host = (parsed_db.hostname or "").lower()
            if db_host and db_host not in ("localhost", "127.0.0.1", "::1"):
                logging.warning(
                    "⚠️  XAVFSIZLIK OGOHLANTIRISHI: Ilova no-production muhitida (APP_ENV=%s, ENVIRONMENT=%s), "
                    "ammo tashqi/remote bazaga (%s) ulanmoqda! Ma'lumotlar xavfsizligiga e'tibor bering.",
                    settings.APP_ENV, getattr(settings, "ENVIRONMENT", None), db_host
                )
        except Exception as e:
            logging.debug("Non-production database host check skipped: %s", e)

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
            try:
                from app.infrastructure.db.session import Base
                import app.infrastructure.db.models
                await conn.run_sync(Base.metadata.create_all)
            except Exception as e:
                logging.warning(f'Auto-create tables info: {e}')
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


def is_origin_allowed(origin: str | None) -> bool:
    """Check if an origin is permitted under strict CORS & CSRF rules."""
    if not origin:
        return False
    origin_clean = origin.rstrip("/")
    # Exact match in CORS_ORIGINS
    if origin_clean in [o.rstrip("/") for o in settings.CORS_ORIGINS]:
        return True
    # Regex match for preview / vercel branches
    if settings.CORS_ORIGIN_REGEX and re.match(settings.CORS_ORIGIN_REGEX, origin_clean):
        return True
    # Local development origins
    if not settings.is_production:
        dev_allowed = {
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:3001",
            "http://127.0.0.1:8000",
            "http://test",
        }
        if origin_clean in dev_allowed:
            return True
    return False


AUTH_COOKIE_NAMES = {"access_token", "user_access_token", "refresh_token"}
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


@app.middleware("http")
async def csrf_origin_protection_middleware(request: Request, call_next):
    """
    CSRF Defense: Strict Origin & Referer Verification for State-Changing Requests.
    1. Safe HTTP methods (GET, HEAD, OPTIONS) bypass CSRF checks.
    2. Any state-changing request (POST, PUT, PATCH, DELETE) with an Origin header
       must match trusted origins (CORS allowed list or same-origin).
    3. If Origin header is absent:
       - If authenticated via ambient auth cookies (access_token, user_access_token, refresh_token):
         Must carry a valid Referer header matching trusted origins; otherwise rejected (403).
       - If no auth cookies present (e.g. Bot with X-Bot-Secret or API with Bearer token):
         Proceeds to router-level authentication.
    """
    if request.method in SAFE_METHODS:
        return await call_next(request)

    origin = request.headers.get("origin")
    referer = request.headers.get("referer")

    request_origin = f"{request.url.scheme}://{request.url.netloc}"
    base_origin = str(request.base_url).rstrip("/")

    # 1. Validate Origin header if present
    if origin:
        origin_clean = origin.rstrip("/")
        if not (is_origin_allowed(origin_clean) or origin_clean == request_origin or origin_clean == base_origin):
            logging.warning(
                "CSRF blocked: untrusted Origin '%s' on %s %s",
                origin, request.method, request.url.path
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF himoyasi: Ruxsat etilmagan Origin (Forbidden Origin)."},
            )
        return await call_next(request)

    # 2. Origin is absent: check for ambient authentication cookies
    has_auth_cookie = any(cookie_name in request.cookies for cookie_name in AUTH_COOKIE_NAMES)
    if has_auth_cookie:
        if referer:
            try:
                from urllib.parse import urlparse
                parsed_ref = urlparse(referer)
                referer_origin = f"{parsed_ref.scheme}://{parsed_ref.netloc}"
                if not (is_origin_allowed(referer_origin) or referer_origin == request_origin or referer_origin == base_origin):
                    logging.warning(
                        "CSRF blocked: untrusted Referer '%s' on %s %s",
                        referer, request.method, request.url.path
                    )
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={"detail": "CSRF himoyasi: Ruxsat etilmagan Referer (Forbidden Referer)."},
                    )
            except Exception:
                logging.warning("CSRF blocked: malformed Referer '%s'", referer)
                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "CSRF himoyasi: Noto'g'ri Referer (Malformed Referer)."},
                )
        else:
            # Cookie-authenticated state-changing request with neither Origin nor Referer
            logging.warning(
                "CSRF blocked: missing Origin and Referer on cookie-authenticated %s %s",
                request.method, request.url.path
            )
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF himoyasi: Origin yoki Referer sarlavhasi talab qilinadi."},
            )

    return await call_next(request)



@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
    logging.exception(f"Unhandled server error [{request_id}] on {request.method} {request.url.path}: {exc}")
    headers = {}
    origin = request.headers.get("origin")
    if is_origin_allowed(origin):
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
        headers["Access-Control-Allow-Headers"] = "*"
        headers["Access-Control-Allow-Methods"] = "*"

    if settings.is_production:
        content = {
            "detail": "Serverda kutilmagan xatolik yuz berdi. Bir ozdan so'ng qayta urinib ko'ring.",
            "request_id": request_id,
        }
    else:
        content = {
            "detail": "Serverda kutilmagan xatolik yuz berdi. Bir ozdan so'ng qayta urinib ko'ring.",
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "request_id": request_id,
        }

    return JSONResponse(
        status_code=500,
        content=content,
        headers=headers,
    )

app.add_middleware(SlowAPIMiddleware)

@app.get("/api/v1/diag")
async def diag(admin: dict = Depends(get_current_admin)):
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
app.include_router(content_requests.router, prefix="/api/v1")
app.include_router(actors.router, prefix="/api/v1")

# ── Static Uploads ───────────────────────────────────────────────
os.makedirs("uploads/reports", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX or None,
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
async def health_check(response: Response) -> dict:
    """
    Comprehensive liveness and readiness probe.
    Executes a fast (<= 2s) DB ping query. If DB fails, returns 503.
    Reports Redis availability and bot supervisor status (alive/degraded/stopped).
    Degraded bot does not fail the overall web health check.
    """
    import asyncio
    from sqlalchemy import text
    from app.core.bot_status import is_bot_alive, get_bot_status
    from app.core.cache import is_redis_available
    import app.infrastructure.db.session as db_session_module

    db_status = "connected"
    try:
        async with db_session_module.async_session_factory() as session:
            await asyncio.wait_for(session.execute(text("SELECT 1")), timeout=5.0)
    except Exception as exc:
        logging.getLogger(__name__).warning("Database health check ping failed: %s", exc)
        db_status = "unavailable"
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    redis_status = "connected" if is_redis_available() else "unavailable"
    bot_status = get_bot_status()
    overall_status = "healthy" if db_status == "connected" else "unhealthy"

    return {
        "status": overall_status,
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "database": db_status,
        "redis": redis_status,
        "bot": bot_status,
        "bot_alive": is_bot_alive(),
    }
