import asyncio, asyncpg

async def check():
    conn = await asyncpg.connect(
        "postgresql://neondb_owner:npg_2eToVwtng7Os@ep-frosty-cherry-aitqstf5.c-4.us-east-1.aws.neon.tech/neondb?ssl=require",
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

asyncio.run(check())
