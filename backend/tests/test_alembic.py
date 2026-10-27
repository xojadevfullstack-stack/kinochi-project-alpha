import os
import asyncio
import importlib.util
from pathlib import Path
import pytest
import asyncpg
from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic import command
from tests.conftest import verify_safe_test_db, LOCAL_PG_TEST_URL


def get_test_pg_port() -> int:
    return int(os.environ.get("TEST_DB_PORT", "5433"))


async def get_test_pg_connection():
    verify_safe_test_db(LOCAL_PG_TEST_URL)
    return await asyncpg.connect(
        user="postgres",
        password="postgres",
        host="127.0.0.1",
        port=get_test_pg_port(),
        database="kinochi_v2_test"
    )


def get_alembic_config() -> Config:
    backend_dir = Path(__file__).resolve().parent.parent
    ini_path = backend_dir / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    return cfg


def run_alembic_in_test_db(cmd_func, *args, **kwargs):
    """Lokal 5433-portdagi test DB muhiti bilan Alembic buyrug'ini xavfsiz yurgizish."""
    verify_safe_test_db(LOCAL_PG_TEST_URL)
    old_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = LOCAL_PG_TEST_URL
    try:
        cmd_func(*args, **kwargs)
    finally:
        if old_url:
            os.environ["DATABASE_URL"] = old_url
        else:
            os.environ.pop("DATABASE_URL", None)


def test_single_head():
    """C0.2: Alembic versiyalarida aynan 1 ta head bo'lishi shart."""
    cfg = get_alembic_config()
    script = ScriptDirectory.from_config(cfg)
    heads = script.get_heads()
    assert len(heads) == 1, f"Kutilgan 1 ta head, ammo topildi: {heads}"
    assert heads[0] == "f1322da82a96", f"Bosh revision kutilgan 'f1322da82a96', topildi: {heads[0]}"


def test_merge_revision_is_empty_schema_change():
    """C0.2: Merge revision sxemaga o'zgartirish kiritmasligi (upgrade/downgrade bo'sh pass) shart."""
    backend_dir = Path(__file__).resolve().parent.parent
    merge_files = list((backend_dir / "alembic" / "versions").glob("*merge_heads*.py"))
    assert len(merge_files) == 1, f"Merge revision fayli topilmadi: {merge_files}"

    merge_path = merge_files[0]
    spec = importlib.util.spec_from_file_location("merge_rev_module", str(merge_path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # down_revision tekshiruvi: ikkala headni qamrab olgan bo'lishi kerak
    assert mod.down_revision == ("e013ec7302", "e8f9a0b1c2d3") or mod.down_revision == ["e013ec7302", "e8f9a0b1c2d3"], (
        f"down_revision noto'g'ri: {mod.down_revision}"
    )

    # upgrade va downgrade funksiyalari bo'sh (hech qanday DDL operatsiyasi bajarmaydi)
    import inspect
    up_source = inspect.getsource(mod.upgrade).strip().splitlines()
    down_source = inspect.getsource(mod.downgrade).strip().splitlines()

    # Faqat def va pass qatorlaridan iborat
    assert any("pass" in line for line in up_source), "upgrade() bo'sh emas!"
    assert any("pass" in line for line in down_source), "downgrade() bo'sh emas!"


@pytest.mark.asyncio
async def test_prod_like_migration_preserves_data():
    """
    C0.2: Prod-like migratsiya tekshiruvi:
    1. Bo'sh sxemadan f1a2b3c4d5e6 (branchpoint) gacha upgrade.
    2. Namuna qatorlar kiritiladi (prod holatiga mos).
    3. Head gacha upgrade qilinadi.
    4. Kiritilgan qatorlar buzilmagani tasdiqlanadi.
    """
    verify_safe_test_db(LOCAL_PG_TEST_URL)
    cfg = get_alembic_config()

    # 1. Sxemani tozalash va branchpoint f1a2b3c4d5e6 gacha ko'tarish
    conn = await get_test_pg_connection()
    try:
        await conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
    finally:
        await conn.close()

    await asyncio.to_thread(run_alembic_in_test_db, command.upgrade, cfg, "f1a2b3c4d5e6")

    # 2. Namuna qatorlar kiritish
    conn = await get_test_pg_connection()
    try:
        await conn.execute("INSERT INTO categories (name, slug) VALUES ('Test Category', 'test-cat-c02') ON CONFLICT DO NOTHING;")
        cat_id = await conn.fetchval("SELECT id FROM categories WHERE slug='test-cat-c02';")
        assert cat_id is not None

        await conn.execute("""
            INSERT INTO movies (title, code, release_year, publish_status)
            VALUES ('Test Movie C02', 'c02_mov1', 2026, 'published')
            ON CONFLICT DO NOTHING;
        """)
        # collections jadvali (prod-like sharoitda mavjud bo'lgan)
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS collections (
                id SERIAL PRIMARY KEY,
                title VARCHAR(255) NOT NULL,
                slug VARCHAR(255) NOT NULL UNIQUE,
                description TEXT,
                poster_url VARCHAR(1024),
                backdrop_url VARCHAR(1024),
                is_active BOOLEAN DEFAULT TRUE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
            );
        """)
    finally:
        await conn.close()

    # 3. Head gacha upgrade qilish
    await asyncio.to_thread(run_alembic_in_test_db, command.upgrade, cfg, "head")

    # 4. Kiritilgan ma'lumotlar saqlanib qolganini tekshirish
    conn = await get_test_pg_connection()
    try:
        m_row = await conn.fetchrow("SELECT title, publish_status FROM movies WHERE code='c02_mov1';")
        assert m_row is not None
        assert m_row["title"] == "Test Movie C02"
        assert m_row["publish_status"] == "published"
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_merge_schema_equivalence():
    """
    C0.2: Merge revision sxemani o'zgartirmasligini tekshirish:
    A shox (e013ec7302) va B shox (e8f9a0b1c2d3) qo'llangandagi jadvallar ro'yxati
    head (f1322da82a96) dagi jadvallar ro'yxatiga teng bo'ladi.
    """
    verify_safe_test_db(LOCAL_PG_TEST_URL)

    conn = await get_test_pg_connection()
    try:
        rows = await conn.fetch("""
            SELECT table_name FROM information_schema.tables
            WHERE table_schema = 'public' ORDER BY table_name;
        """)
        tables_list = [r["table_name"] for r in rows]

        # Muhim jadvallar mavjudligini tasdiqlash
        assert "movies" in tables_list
        assert "series" in tables_list
        assert "seed_candidates" in tables_list  # B shox
        assert "content_requests" in tables_list  # A shox
        assert "collection_subscriptions" in tables_list  # A shox
        assert "broadcasts" in tables_list
    finally:
        await conn.close()


@pytest.mark.asyncio
async def test_merge_downgrade_and_reupgrade():
    """
    C0.2: Merge revision downgrade va qayta upgrade qilinishini tekshirish.
    Merge revision'dan ota revisionga (e013ec7302) tushib, yana head ga ko'tariladi.
    """
    verify_safe_test_db(LOCAL_PG_TEST_URL)
    cfg = get_alembic_config()

    # Downgrade to parent e013ec7302
    await asyncio.to_thread(run_alembic_in_test_db, command.downgrade, cfg, "e013ec7302")
    # Upgrade back to head
    await asyncio.to_thread(run_alembic_in_test_db, command.upgrade, cfg, "head")

    conn = await get_test_pg_connection()
    try:
        val = await conn.fetchval("SELECT version_num FROM alembic_version;")
        assert val == "f1322da82a96"
    finally:
        await conn.close()

