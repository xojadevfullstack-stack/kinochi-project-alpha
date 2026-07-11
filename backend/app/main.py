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


# ── Lifespan (startup / shutdown hooks) ──────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup / shutdown lifecycle manager."""
    import logging
    logger = logging.getLogger("uvicorn.error")
    logger.info("Running DB migrations...")
    try:
        from alembic.config import Config
        from alembic import command
        import asyncio
        import os
        
        def run_upgrade():
            # ensure we are in the backend directory where alembic.ini is
            # usually the current working dir is backend
            alembic_cfg = Config("alembic.ini")
            command.upgrade(alembic_cfg, "head")
            
        await asyncio.to_thread(run_upgrade)
        logger.info("DB migrations completed.")
    except Exception as e:
        logger.error(f"Failed to run migrations: {e}")

    yield
    # Cleanup resources on shutdown


from app.api.v1 import movies, categories, users, channels, auth, broadcasts, uploads, series
from fastapi.staticfiles import StaticFiles
import os

# Create uploads directory if it doesn't exist
os.makedirs("uploads/posters", exist_ok=True)

# ── App factory ──────────────────────────────────────────────────
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ── Mount Static Files ───────────────────────────────────────────
app.mount("/static", StaticFiles(directory="uploads"), name="static")

# ── Routers ──────────────────────────────────────────────────────
app.include_router(movies.router, prefix="/api/v1")
app.include_router(series.router, prefix="/api/v1")
app.include_router(categories.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(channels.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(broadcasts.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")

# ── CORS ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
