"""
Kinochi Backend — FastAPI application entrypoint.

Presentation Layer: This is the top-level composition root that wires
together all routers, middleware, and lifecycle hooks.  No business
logic lives here.
"""

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.api.v1 import movies, categories, users, channels, auth, broadcasts, series, sources

# ── Lifespan (startup / shutdown hooks) ──────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle manager."""
    import asyncio
    import os
    import httpx
    import logging

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

    task = asyncio.create_task(keep_alive())
    yield
    task.cancel()


# ── App factory ──────────────────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Routers ──────────────────────────────────────────────────────
app.include_router(movies.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(channels.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(broadcasts.router, prefix="/api/v1")
app.include_router(series.router, prefix="/api/v1")
app.include_router(sources.router, prefix="/api/v1/sources", tags=["sources"])

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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
