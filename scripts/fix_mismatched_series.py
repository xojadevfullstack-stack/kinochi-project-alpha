import os
import sys
import asyncio
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))

from app.infrastructure.db.session import async_session_factory
from app.core.cache import delete_cache_pattern
from sqlalchemy import text

FIXES = [
    {
        "id": 1007,
        "title": "Kontinental: Jon Uik dunyosida",
        "tmdb_id": 72710,
        "poster_url": "https://image.tmdb.org/t/p/w500/2urdwqEL9FRkGMKAkhfvWTALG00.jpg"
    },
    {
        "id": 1015,
        "title": "Persi Jekson va olimpiyachilar",
        "tmdb_id": 103540,
        "poster_url": "https://image.tmdb.org/t/p/w500/bd5ZIqiz1PRiLC7FLexzVBf8qu1.jpg"
    },
    {
        "id": 1017,
        "title": "Shtamm",
        "tmdb_id": 47640,
        "poster_url": "https://image.tmdb.org/t/p/w500/2BWErT9QcADpf2G4BZ769eSnFTP.jpg"
    },
    {
        "id": 1022,
        "title": "The Originals (Haqiqiylar)",
        "tmdb_id": 46896,
        "poster_url": "https://image.tmdb.org/t/p/w500/keJOhJXGiLL54EW6QocbyvQGquA.jpg"
    }
]

async def main():
    async with async_session_factory() as session:
        for f in FIXES:
            print(f"Updating series {f['id']} ({f['title']}) -> tmdb_id={f['tmdb_id']}, poster={f['poster_url']}")
            await session.execute(
                text("UPDATE series SET tmdb_id = :tmdb_id, poster_url = :poster_url WHERE id = :id"),
                {"id": f["id"], "tmdb_id": f["tmdb_id"], "poster_url": f["poster_url"]}
            )
        await session.commit()
        print("Updated series successfully committed!")
    
    # Invalidate cache
    try:
        await delete_cache_pattern("*")
        print("Redis cache flushed!")
    except Exception as e:
        print(f"Cache flush notice: {e}")

if __name__ == "__main__":
    asyncio.run(main())
