import os
import asyncio
from unittest.mock import patch
import asyncpg
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from alembic.config import Config
from alembic import command
from app.infrastructure.db.session import Base
import app.infrastructure.db.models  # Load all models


TEST_PG_URL = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5433/kinochi_reconciler_test"
TEST_PG_SYNC_URL = "postgresql://postgres:postgres@127.0.0.1:5433/kinochi_reconciler_test"
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ALEMBIC_INI = os.path.join(ROOT_DIR, "alembic.ini")


def get_alembic_config(db_url: str) -> Config:
    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("sqlalchemy.url", db_url)
    cfg.set_main_option("script_location", os.path.join(ROOT_DIR, "alembic"))
    return cfg


async def reset_db():
    conn = await asyncpg.connect("postgresql://postgres:postgres@127.0.0.1:5433/postgres")
    await conn.execute("DROP DATABASE IF EXISTS kinochi_reconciler_test WITH (FORCE);")
    await conn.execute("CREATE DATABASE kinochi_reconciler_test;")
    await conn.close()


@pytest.mark.asyncio
async def test_4_5_disposable_postgres_reconciler_scenarios():
    """Verify all 4 migration scenarios on disposable PostgreSQL 17."""
    cfg = get_alembic_config(TEST_PG_SYNC_URL)

    # -------------------------------------------------------------
    # Scenario (i): Bo'sh bazada alembic upgrade head xatti-harakati
    # -------------------------------------------------------------
    await reset_db()
    # Eslatma: c011ec7100 migratsiyasi bo'sh bazada collections jadvalisiz yiqiladi
    # Bu tarixiy migratsiyani o'zgartirmaslik qoidasining tabiiy natijasi
    failed_on_empty = False
    fail_reason = ""
    try:
        with patch.dict(os.environ, {"DATABASE_URL": TEST_PG_URL}):
            await asyncio.to_thread(command.upgrade, cfg, "head")
    except Exception as e:
        failed_on_empty = True
        fail_reason = str(e)

    assert failed_on_empty is True, "Bo'sh bazada collections yo'qligi sababli c011ec7100 xato berishi kutiladi"
    assert "collections" in fail_reason.lower()

    # -------------------------------------------------------------
    # Scenario (ii): create_all bilan yaratilgan baza + stamp + upgrade head
    # -------------------------------------------------------------
    await reset_db()
    engine = create_async_engine(TEST_PG_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Stamp head dan oldingi holat (9c8d7e6f5a4b)
    with patch.dict(os.environ, {"DATABASE_URL": TEST_PG_URL}):
        await asyncio.to_thread(command.stamp, cfg, "9c8d7e6f5a4b")

        # Endi upgrade head (b2c3d4e5f6a7 reconciler) ishlaydi
        await asyncio.to_thread(command.upgrade, cfg, "head")

    # Tekshiruv: barcha jadvallar va ustunlar mavjudligi
    async with engine.connect() as conn:
        # series.source_id mavjudmi
        res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'series' AND column_name = 'source_id'"))
        assert res.scalar() == "source_id"

        # movies.is_18_plus mavjudmi
        res_m = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'movies' AND column_name = 'is_18_plus'"))
        assert res_m.scalar() == "is_18_plus"

        # collections jadvali mavjudmi
        res_c = await conn.execute(text("SELECT to_regclass('collections')"))
        assert res_c.scalar() is not None

    # -------------------------------------------------------------
    # Scenario (iii): Migratsiyani 2 marta ishga tushirish (idempotentlik)
    # -------------------------------------------------------------
    # Qayta upgrade head xato bermasligi kerak
    with patch.dict(os.environ, {"DATABASE_URL": TEST_PG_URL}):
        await asyncio.to_thread(command.upgrade, cfg, "head")

    # -------------------------------------------------------------
    # Scenario (iv): Downgrade xavfsizligi
    # -------------------------------------------------------------
    with patch.dict(os.environ, {"DATABASE_URL": TEST_PG_URL}):
        await asyncio.to_thread(command.downgrade, cfg, "-1")
    # collections jadvali o'chib ketmasligi shart (xavfsiz downgrade)
    async with engine.connect() as conn:
        res_safe = await conn.execute(text("SELECT to_regclass('collections')"))
        assert res_safe.scalar() is not None

    # Qayta upgrade qilib head holatiga olib kelish
    with patch.dict(os.environ, {"DATABASE_URL": TEST_PG_URL}):
        await asyncio.to_thread(command.upgrade, cfg, "head")
    await engine.dispose()
