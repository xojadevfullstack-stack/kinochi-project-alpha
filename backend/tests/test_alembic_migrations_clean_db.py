import pytest
import os
import asyncio
import asyncpg
from unittest.mock import patch
from alembic.config import Config
from alembic import command

CLEAN_DB_URL = "postgresql+asyncpg://postgres:postgres@localhost:5433/kinochi_v2_clean_test"

@pytest.mark.asyncio
async def test_alembic_migration_c011ec7100_requires_collections_table():
    """
    BUG-003 Regression Test:
    Running migration c011ec7100 on an empty database must succeed without
    'relation "collections" does not exist' error.
    """
    # 1. Reset empty database
    admin_conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5433/postgres")
    try:
        await admin_conn.execute("DROP DATABASE IF EXISTS kinochi_v2_clean_test;")
        await admin_conn.execute("CREATE DATABASE kinochi_v2_clean_test;")
    finally:
        await admin_conn.close()

    # 2. Configure Alembic
    alembic_cfg = Config("backend/alembic.ini")
    alembic_cfg.set_main_option("script_location", "backend/alembic")
    alembic_cfg.set_main_option("sqlalchemy.url", CLEAN_DB_URL)

    # 3. Upgrade all the way to head on a completely empty database
    try:
        with patch.dict(os.environ, {"DATABASE_URL": CLEAN_DB_URL}):
            # Full upgrade to head
            await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
            # Downgrade 1 step
            await asyncio.to_thread(command.downgrade, alembic_cfg, "-1")
            # Re-upgrade to head
            await asyncio.to_thread(command.upgrade, alembic_cfg, "head")
    finally:
        # Cleanup clean DB
        admin_conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5433/postgres")
        try:
            await admin_conn.execute("DROP DATABASE IF EXISTS kinochi_v2_clean_test;")
        finally:
            await admin_conn.close()
