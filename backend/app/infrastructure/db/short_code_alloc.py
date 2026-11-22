"""Shared collision-free short_code allocator across movies and episodes."""
from __future__ import annotations

from sqlalchemy import or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import EpisodeModel


async def next_global_short_code(session: AsyncSession) -> str:
    """Allocate the next unused numeric short_code across both movies and episodes."""
    bind = session.get_bind()
    if bind is not None and "postgres" in bind.dialect.name:
        await session.execute(text("SELECT pg_advisory_xact_lock(90210)"))

    m_vals = (await session.execute(select(MovieModel.short_code).where(MovieModel.short_code.isnot(None)))).scalars().all()
    e_vals = (await session.execute(select(EpisodeModel.short_code).where(EpisodeModel.short_code.isnot(None)))).scalars().all()
    nums = [
        int(val)
        for val in (*m_vals, *e_vals)
        if val and val.isdigit() and int(val) < 1_000_000
    ]
    candidate = max(nums, default=1000) + 1

    while True:
        key = str(candidate)
        m_hit = (
            await session.execute(
                select(MovieModel.id).where(or_(MovieModel.short_code == key, MovieModel.code == key)).limit(1)
            )
        ).scalar_one_or_none()
        e_hit = (
            await session.execute(
                select(EpisodeModel.id).where(or_(EpisodeModel.short_code == key, EpisodeModel.code == key)).limit(1)
            )
        ).scalar_one_or_none()
        if m_hit is None and e_hit is None:
            return key
        candidate += 1
