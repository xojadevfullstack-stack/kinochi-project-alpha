"""
Bu script alembic_version ni tekshirib, agar 'pages' jadvali allaqachon
mavjud bo'lsa lekin alembic versiyasi eski bo'lsa — uni to'g'irlaydi.

Render'da deploy bo'lganda 'alembic upgrade head' qayta ishga tushmaydi,
chunki alembic_version allaqachon eng oxirgisida bo'ladi.
"""
import asyncio
import asyncpg
import os
import sys

DATABASE_URL = os.getenv("DATABASE_URL", "")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL environment variable not set")
    sys.exit(1)

# asyncpg uchun postgresql+asyncpg -> postgresql
url = DATABASE_URL.replace("postgresql+asyncpg", "postgresql")
# ssl=require -> ?ssl=require ga aylantirish
if "?ssl=require" in url:
    url = url  # already has ssl param
elif "ssl=require" in url:
    url = url

async def fix_alembic_version():
    print(f"Connecting to database...")
    conn = await asyncpg.connect(url, timeout=30)
    try:
        # Hozirgi alembic versiyasini ko'rish
        rows = await conn.fetch("SELECT version_num FROM alembic_version")
        current = rows[0]["version_num"] if rows else None
        print(f"Current alembic_version: {current}")
        
        # pages jadvali mavjudmi?
        pages_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='pages' AND table_schema='public')"
        )
        print(f"'pages' table exists: {pages_exists}")
        
        # page_movie jadvali mavjudmi?
        page_movie_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name='page_movie' AND table_schema='public')"
        )
        print(f"'page_movie' table exists: {page_movie_exists}")
        
        TARGET_VERSION = "8e4e155f48db"
        
        if pages_exists and page_movie_exists and current != TARGET_VERSION:
            print(f"Fixing: pages jadvali mavjud, lekin version {current}. {TARGET_VERSION} ga yangilanmoqda...")
            if rows:
                await conn.execute(
                    "UPDATE alembic_version SET version_num = $1", TARGET_VERSION
                )
            else:
                await conn.execute(
                    "INSERT INTO alembic_version (version_num) VALUES ($1)", TARGET_VERSION
                )
            print(f"✅ alembic_version -> {TARGET_VERSION} ga yangilandi!")
        elif current == TARGET_VERSION:
            print(f"✅ alembic_version allaqachon to'g'ri: {TARGET_VERSION}")
        else:
            print(f"ℹ️  pages jadvali yo'q — oddiy migration ishlashi kerak")
            
    except Exception as e:
        print(f"ERROR: {e}")
        raise
    finally:
        await conn.close()
        print("Connection closed.")

if __name__ == "__main__":
    asyncio.run(fix_alembic_version())
