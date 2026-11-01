"""
Postgres'da FOR UPDATE SKIP LOCKED claim_next parallel xavfsizligi testi.
TEST_POSTGRES_URL env'i berilmasa yoki localhost + 'test' db nomi bo'lmasa skip qilinadi.
Vaqtinchalik alohida sxema (ingest_claim_<hex>) ichida yaratiladi va o'chiriladi;
public.ingest_items ga hech qachon tegmaydi.
"""
import asyncio
import os
import uuid
from urllib.parse import urlparse

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.application.ingest_service import IngestService
from app.infrastructure.db.models.ingest_item import IngestItemModel

N_ITEMS = 20
N_WORKERS = 8


def _get_safe_test_postgres_url() -> str:
    url = os.environ.get("TEST_POSTGRES_URL", "").strip()
    if not url:
        pytest.skip("TEST_POSTGRES_URL berilmagan: Postgres claim testi o'tkazib yuborildi")

    clean = url.replace("postgresql+asyncpg://", "http://").replace("postgres://", "http://").replace("postgresql://", "http://")
    parsed = urlparse(clean)
    host = (parsed.hostname or "").lower()
    db_name = (parsed.path or "").lstrip("/").split("?")[0]

    if host not in ("localhost", "127.0.0.1", "::1"):
        pytest.skip(f"TEST_POSTGRES_URL host localhost emas ({host!r}): test o'tkazib yuborildi")

    if "test" not in db_name.lower():
        pytest.skip(f"TEST_POSTGRES_URL baza nomida 'test' yo'q ({db_name!r}): test o'tkazib yuborildi")

    return url


def test_claim_postgres_guard_skips_unsafe_urls(monkeypatch):
    monkeypatch.delenv("TEST_POSTGRES_URL", raising=False)
    with pytest.raises(pytest.skip.Exception, match="TEST_POSTGRES_URL berilmagan"):
        _get_safe_test_postgres_url()

    monkeypatch.setenv("TEST_POSTGRES_URL", "postgresql+asyncpg://u:p@ep-neon.aws.neon.tech/kinochi_test")
    with pytest.raises(pytest.skip.Exception, match="localhost emas"):
        _get_safe_test_postgres_url()

    monkeypatch.setenv("TEST_POSTGRES_URL", "postgresql+asyncpg://u:p@localhost:5432/kinochi_prod")
    with pytest.raises(pytest.skip.Exception, match="baza nomida 'test' yo'q"):
        _get_safe_test_postgres_url()


@pytest.mark.asyncio
async def test_parallel_claim_next_never_double_claims():
    url = _get_safe_test_postgres_url()
    schema_name = f"ingest_claim_{uuid.uuid4().hex[:8]}"

    try:
        base_engine = create_async_engine(url, echo=False)
        async with base_engine.begin() as conn:
            await conn.execute(text(f'CREATE SCHEMA "{schema_name}"'))
    except Exception as e:
        pytest.skip(f"TEST_POSTGRES_URL database unreachable or schema create failed: {e}")

    isolated_engine = base_engine.execution_options(
        schema_translate_map={None: schema_name, "public": schema_name}
    )
    factory = async_sessionmaker(isolated_engine, class_=AsyncSession, expire_on_commit=False)

    try:
        async with isolated_engine.begin() as conn:
            await conn.run_sync(IngestItemModel.__table__.create)

        async with factory() as session:
            service = IngestService(session)
            added = await service.add_batch([
                {"source": "uzmovi", "source_id": str(i), "title": f"Item {i}", "status": "queued"}
                for i in range(N_ITEMS)
            ])
            await session.commit()
            assert added == N_ITEMS

        async def worker(idx: int) -> list:
            claimed = []
            while True:
                async with factory() as session:
                    service = IngestService(session)
                    item = await service.claim_next(worker_id=f"w{idx}")
                    if item is None:
                        return claimed
                    claimed.append(item.id)
                await asyncio.sleep(0)

        results = await asyncio.gather(*(worker(i) for i in range(N_WORKERS)))
        all_ids = [i for r in results for i in r]

        assert len(all_ids) == len(set(all_ids)), "Bitta item ikki marta claim qilingan"
        assert len(all_ids) == N_ITEMS
    finally:
        async with base_engine.begin() as conn:
            await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
        await base_engine.dispose()
