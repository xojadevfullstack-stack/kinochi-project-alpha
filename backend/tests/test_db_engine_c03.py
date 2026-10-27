import asyncio
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import Settings
from app.infrastructure.db.session import get_engine_kwargs
from tests.conftest import verify_safe_test_db, LOCAL_PG_TEST_URL


def test_engine_kwargs_connect_args_and_dialect_isolation():
    """
    C0.3: Engine kwargs unit-test:
    - asyncpg URL uchun: connect_args (statement_cache_size=0, prepared_statement_cache_size=0,
      prepared_statement_name_func) mavjud.
    - sqlite URL uchun: connect_args va pool_size umuman qo'llanmaydi.
    """
    pg_url = "postgresql+asyncpg://postgres:postgres@localhost:5433/kinochi_v2_test"
    pg_kwargs = get_engine_kwargs(pg_url)

    assert "connect_args" in pg_kwargs
    connect_args = pg_kwargs["connect_args"]
    assert connect_args["statement_cache_size"] == 0
    assert connect_args["prepared_statement_cache_size"] == 0
    assert callable(connect_args["prepared_statement_name_func"])

    name1 = connect_args["prepared_statement_name_func"]()
    name2 = connect_args["prepared_statement_name_func"]()
    assert name1.startswith("__asyncpg_")
    assert name2.startswith("__asyncpg_")
    assert name1 != name2, "Har bir prepared statement nomi unique bo'lishi kerak!"

    # SQLite tekshiruvi: connect_args va pool parametrlari bo'lmasligi shart
    sqlite_url = "sqlite+aiosqlite:///:memory:"
    sqlite_kwargs = get_engine_kwargs(sqlite_url)
    assert "connect_args" not in sqlite_kwargs
    assert "pool_size" not in sqlite_kwargs
    assert "max_overflow" not in sqlite_kwargs


def test_pool_defaults_and_custom_override():
    """
    C0.3: DB_POOL_SIZE va DB_MAX_OVERFLOW default 10/20,
    hamda sozlanishi tekshiriladi.
    """
    assert Settings.model_fields["DB_POOL_SIZE"].default == 10
    assert Settings.model_fields["DB_MAX_OVERFLOW"].default == 20

    pg_url = "postgresql+asyncpg://postgres:postgres@localhost:5433/kinochi_v2_test"
    default_kwargs = get_engine_kwargs(pg_url)
    assert default_kwargs["pool_size"] == 10
    assert default_kwargs["max_overflow"] == 20
    assert default_kwargs["pool_pre_ping"] is True
    assert default_kwargs["pool_recycle"] == 300

    custom_kwargs = get_engine_kwargs(pg_url, pool_size=25, max_overflow=50)
    assert custom_kwargs["pool_size"] == 25
    assert custom_kwargs["max_overflow"] == 50


@pytest.mark.asyncio
async def test_local_postgres_parallel_queries_with_pooler_safe_engine():
    """
    C0.3: Lokal PostgreSQL (localhost:5433, kinochi_v2_test) da
    pooler-xavfsiz engine bilan kamida 20 ta parallel so'rov muvaffaqiyatli o'tishi.
    """
    verify_safe_test_db(LOCAL_PG_TEST_URL)

    engine_kwargs = get_engine_kwargs(LOCAL_PG_TEST_URL, pool_size=10, max_overflow=20)
    test_engine = create_async_engine(LOCAL_PG_TEST_URL, **engine_kwargs)

    async def execute_task(idx: int):
        async with test_engine.connect() as conn:
            res = await conn.execute(text(f"SELECT {idx} AS task_num, 'ok' AS status"))
            row = res.mappings().one()
            return row["task_num"], row["status"]

    try:
        # Kamida 25 ta parallel so'rov
        tasks = [execute_task(i) for i in range(25)]
        results = await asyncio.gather(*tasks)

        assert len(results) == 25
        for i, (task_num, status) in enumerate(results):
            assert task_num == i
            assert status == "ok"
    finally:
        await test_engine.dispose()
