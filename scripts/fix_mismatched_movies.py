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
        "id": 974,
        "title": "Bir vaqtlar Anadoluda",
        "tmdb_id": 74879,
        "poster_url": "https://image.tmdb.org/t/p/w500/bN84guFndgvtWIvFC7sTD8AAJDE.jpg"
    },
    {
        "id": 975,
        "title": "12 Stul",
        "tmdb_id": 31648,
        "poster_url": "https://image.tmdb.org/t/p/w500/fVzfgLPgrEOti2svUqwyLCtIeML.jpg"
    },
    {
        "id": 976,
        "title": "Jajji Guvoh",
        "tmdb_id": 570508,
        "poster_url": "https://image.tmdb.org/t/p/w500/rLfGdUJ4Rp1FTWKOvaZlMqHXb4i.jpg"
    },
    {
        "id": 983,
        "title": "Supermen (2025)",
        "tmdb_id": 1061474,
        "poster_url": "https://image.tmdb.org/t/p/w500/ldyfo0BKmz5rWtJJKCvwaNS4cJT.jpg"
    },
    {
        "id": 997,
        "title": "Aura: Koga Maryuinning so‘nggi jangi",
        "tmdb_id": 225086,
        "poster_url": "https://image.tmdb.org/t/p/w500/4A4xhymZbWTUeCf90uXipurbARB.jpg"
    },
    {
        "id": 1000,
        "title": "Seni doim sevganman",
        "tmdb_id": 374853,
        "poster_url": "https://image.tmdb.org/t/p/w500/rQDnIuWMYdZ2BXwaqy4Ird4w8Kw.jpg"
    }
]

async def main():
    async with async_session_factory() as session:
        for f in FIXES:
            print(f"Updating movie {f['id']} ({f['title']}) -> tmdb_id={f['tmdb_id']}, poster={f['poster_url']}")
            await session.execute(
                text("UPDATE movies SET tmdb_id = :tmdb_id, poster_url = :poster_url WHERE id = :id"),
                {"id": f["id"], "tmdb_id": f["tmdb_id"], "poster_url": f["poster_url"]}
            )
        await session.commit()
        print("Updated movies successfully committed!")
    
    # Invalidate cache
    try:
        await delete_cache_pattern("*")
        print("Redis cache flushed!")
    except Exception as e:
        print(f"Cache flush notice: {e}")

if __name__ == "__main__":
    asyncio.run(main())
