"""
Postgres'da FOR UPDATE SKIP LOCKED claim_next parallel xavfsizligi testi.
TEST_POSTGRES_URL env'i berilmasa skip qilinadi. Faqat localhost ga ruxsat.
"""
import asyncio
import os
from urllib.parse import urlparse

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.ingest_service import IngestService
from app.infrastructure.db.models.ingest_item import IngestItemModel

TEST_POSTGRES_URL = os.environ.get("TEST_POSTGRES_URL")

pytestmark = pytest.mark.skipif(
    not TEST_POSTGRES_URL,
    reason="TEST_POSTGRES_URL berilmagan: Postgres claim testi o'tkazib yuborildi",
)

N_ITEMS = 20
N_WORKERS = 8


def _assert_localhost_only(url: str) -> None:
    clean = url.replace("postgresql+asyncpg://", "http://").replace("postgres://", "http://")
    host = urlparse(clean).hostname
    if host not in ("localhost", "127.0.0.1", "::1"):
        raise RuntimeError(f"XAVF: faqat localhost ga ruxsat, berilgan host: {host!r}")


@pytest.mark.asyncio
async def test_parallel_claim_next_never_double_claims():
    _assert_localhost_only(TEST_POSTGRES_URL)
    engine = create_async_engine(TEST_POSTGRES_URL, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(IngestItemModel.__table__.drop, checkfirst=True)
        await conn.run_sync(IngestItemModel.__table__.create)

    try:
        async with factory() as session:
            added = await IngestService(session).add_batch([
                {"source": "uzmovi", "source_id": str(i), "title": f"Item {i}", "status": "queued"}
                for i in range(N_ITEMS)
            ])
            assert added == N_ITEMS

        async def worker(idx: int) -> list:
            claimed = []
            while True:
                async with factory() as session:
                    item = await IngestService(session).claim_next(worker_id=f"w{idx}")
                    if item is None:
                        return claimed
                    claimed.append(item.id)
                await asyncio.sleep(0)

        results = await asyncio.gather(*(worker(i) for i in range(N_WORKERS)))
        all_ids = [i for r in results for i in r]

        assert len(all_ids) == len(set(all_ids)), "Bitta item ikki marta claim qilingan"
        assert len(all_ids) == N_ITEMS
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(IngestItemModel.__table__.drop, checkfirst=True)
        await engine.dispose()
