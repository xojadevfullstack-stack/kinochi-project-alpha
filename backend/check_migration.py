import os
import sys
import asyncio
import asyncpg

DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("XATO: DATABASE_URL yoki TEST_DATABASE_URL muhit o'zgaruvchisi o'rnatilmagan.")
    sys.exit(1)
DATABASE_URL = DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

async def check():
    conn = await asyncpg.connect(
        DATABASE_URL,
        timeout=15
    )
    try:
        # alembic_version
        rows = await conn.fetch("SELECT version_num FROM alembic_version")
        print("Alembic version in DB:", rows)
        
        # pages table mavjudmi?
        exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='pages' AND table_schema='public')"
        )
        print("pages table exists:", exists)
        
        # page_movie mavjudmi?
        exists2 = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='page_movie' AND table_schema='public')"
        )
        print("page_movie table exists:", exists2)
        
        # series_sources mavjudmi?
        exists3 = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='series_sources' AND table_schema='public')"
        )
        print("series_sources table exists:", exists3)
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(check())
