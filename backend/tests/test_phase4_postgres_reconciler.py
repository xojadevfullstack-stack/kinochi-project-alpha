import os
import asyncio
import socket
from urllib.parse import urlparse
from unittest.mock import patch
import asyncpg
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from alembic.config import Config
from alembic import command
from app.infrastructure.db.session import Base
import app.infrastructure.db.models  # noqa: F401  # Load all models


ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ALEMBIC_INI = os.path.join(ROOT_DIR, "alembic.ini")


def _is_port_open(host: str, port: int) -> bool:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(0.5)
        res = s.connect_ex((host, port))
        s.close()
        return res == 0
    except Exception:
        return False


def _resolve_pg_config():
    """
    Resolve test PostgreSQL connection parameters dynamically.
    Checks TEST_DATABASE_URL / TEST_POSTGRES_URL / TEST_DB_PORT / standard ports.
    Safely skips if not localhost or unreachable.
    """
    raw_url = os.environ.get("TEST_POSTGRES_URL") or os.environ.get("TEST_DATABASE_URL") or ""
    if raw_url:
        clean = raw_url.replace("postgresql+asyncpg://", "http://").replace("postgres://", "http://").replace("postgresql://", "http://")
        parsed = urlparse(clean)
        host = (parsed.hostname or "127.0.0.1").lower()
        port = parsed.port or int(os.environ.get("TEST_DB_PORT", "5432"))
        user = parsed.username or "postgres"
        password = parsed.password or "postgres"
    else:
        host = os.environ.get("TEST_DB_HOST", "127.0.0.1").lower()
        user = os.environ.get("TEST_DB_USER", "postgres")
        password = os.environ.get("TEST_DB_PASSWORD", "postgres")
        if "TEST_DB_PORT" in os.environ:
            port = int(os.environ["TEST_DB_PORT"])
        elif _is_port_open("127.0.0.1", 5433):
            port = 5433
        elif _is_port_open("127.0.0.1", 5432):
            port = 5432
        else:
            port = 5432

    if host not in ("localhost", "127.0.0.1", "::1"):
        pytest.skip(f"Safety guard: host '{host}' is not localhost; skipping reconciler integration test.")

    if not _is_port_open(host, port):
        pytest.skip(f"Test PostgreSQL port {host}:{port} is closed; skipping reconciler integration test.")

    admin_url = f"postgresql://{user}:{password}@{host}:{port}/postgres"
    test_pg_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/kinochi_reconciler_test"
    test_pg_sync_url = f"postgresql://{user}:{password}@{host}:{port}/kinochi_reconciler_test"
    return host, port, user, password, admin_url, test_pg_url, test_pg_sync_url


def get_alembic_config(db_url: str) -> Config:
    cfg = Config(ALEMBIC_INI)
    cfg.set_main_option("sqlalchemy.url", db_url)
    cfg.set_main_option("script_location", os.path.join(ROOT_DIR, "alembic"))
    return cfg


async def reset_db(admin_url: str):
    try:
        conn = await asyncpg.connect(admin_url, timeout=2.0)
    except Exception as e:
        pytest.skip(f"Could not connect to PostgreSQL admin database at {admin_url}: {e}")
    try:
        await conn.execute("DROP DATABASE IF EXISTS kinochi_reconciler_test WITH (FORCE);")
        await conn.execute("CREATE DATABASE kinochi_reconciler_test;")
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_4_5_disposable_postgres_reconciler_scenarios():
    """Verify all 4 migration scenarios on disposable PostgreSQL 17."""
    host, port, user, password, admin_url, test_pg_url, test_pg_sync_url = _resolve_pg_config()
    cfg = get_alembic_config(test_pg_sync_url)

    # -------------------------------------------------------------
    # Scenario (i): Bo'sh bazada alembic upgrade head xatti-harakati
    # -------------------------------------------------------------
    await reset_db(admin_url)
    # Eslatma: BUG-003 tuzatilgach, c011ec7100 migratsiyasi collections jadvalini yaratadi
    # va bo'sh bazada alembic upgrade head 100% muvaffaqiyatli o'tadi.
    failed_on_empty = False
    fail_reason = ""
    try:
        with patch.dict(os.environ, {"DATABASE_URL": test_pg_url}):
            await asyncio.to_thread(command.upgrade, cfg, "head")
    except Exception as e:
        failed_on_empty = True
        fail_reason = str(e)

    assert failed_on_empty is False, f"Bo'sh bazada upgrade head muvaffaqiyatli bo'lishi shart, xato: {fail_reason}"

    # -------------------------------------------------------------
    # Scenario (ii): create_all bilan yaratilgan baza + stamp + upgrade head
    # -------------------------------------------------------------
    await reset_db(admin_url)
    engine = create_async_engine(test_pg_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Stamp head dan oldingi holat (9c8d7e6f5a4b)
    with patch.dict(os.environ, {"DATABASE_URL": test_pg_url}):
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
    with patch.dict(os.environ, {"DATABASE_URL": test_pg_url}):
        await asyncio.to_thread(command.upgrade, cfg, "head")

    # -------------------------------------------------------------
    # Scenario (iv): Downgrade xavfsizligi
    # -------------------------------------------------------------
    with patch.dict(os.environ, {"DATABASE_URL": test_pg_url}):
        await asyncio.to_thread(command.downgrade, cfg, "-1")
    # collections jadvali o'chib ketmasligi shart (xavfsiz downgrade)
    async with engine.connect() as conn:
        res_safe = await conn.execute(text("SELECT to_regclass('collections')"))
        assert res_safe.scalar() is not None

    # Qayta upgrade qilib head holatiga olib kelish
    with patch.dict(os.environ, {"DATABASE_URL": test_pg_url}):
        await asyncio.to_thread(command.upgrade, cfg, "head")
    await engine.dispose()


@pytest.mark.asyncio
async def test_reconciler_with_orphan_series_source_id():
    """
    Yetim (orphan) series.source_id qatorlari bo'lgan holatda
    reconciler migratsiyasi (b2c3d4e5f6a7) xatosiz o'tishi va
    NOT VALID constraint qo'shilishi tekshiriladi.
    """
    host, port, user, password, admin_url, test_pg_url, test_pg_sync_url = _resolve_pg_config()
    cfg = get_alembic_config(test_pg_sync_url)

    await reset_db(admin_url)
    engine = create_async_engine(test_pg_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Drop any existing FK constraints to simulate historical drift before b2c3d4e5f6a7
        await conn.execute(text("ALTER TABLE series DROP CONSTRAINT IF EXISTS series_source_id_fkey"))
        await conn.execute(text("ALTER TABLE series DROP CONSTRAINT IF EXISTS fk_series_source_id"))
        # Insert orphan row in series
        await conn.execute(text("""
            INSERT INTO series (title, status, source_id, created_at, updated_at)
            VALUES ('Orphan Test Series', 'ongoing', 999999, now(), now())
        """))

    with patch.dict(os.environ, {"DATABASE_URL": test_pg_url}):
        await asyncio.to_thread(command.stamp, cfg, "9c8d7e6f5a4b")
        # Upgrade head b2c3d4e5f6a7 (orphan qator bo'lsa ham yiqilmasligi shart)
        await asyncio.to_thread(command.upgrade, cfg, "head")

    # Tekshiruv: constraint mavjud va convalidated = False (chunki orphan bor)
    async with engine.connect() as conn:
        res = await conn.execute(text("""
            SELECT conname, convalidated
            FROM pg_constraint
            WHERE conname = 'fk_series_source_id'
        """))
        row = res.fetchone()
        assert row is not None, "fk_series_source_id constraint yaratilishi shart"
        assert row[1] is False, "Orphan qator borligi sababli constraint NOT VALID (convalidated=False) bo'lishi kerak"

        # Yangi noto'g'ri FK yozish urinishi bloklanishi kerak
        with pytest.raises(Exception):
            await conn.execute(text("""
                INSERT INTO series (title, status, source_id, created_at, updated_at)
                VALUES ('Second Invalid Series', 'ongoing', 888888, now(), now())
            """))

    # Qayta upgrade qilish idempotent ekanligi (duplicate_object exception handling)
    with patch.dict(os.environ, {"DATABASE_URL": test_pg_url}):
        await asyncio.to_thread(command.upgrade, cfg, "head")

    await engine.dispose()
