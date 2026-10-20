import asyncio
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as conn:
        movies = (await conn.execute(text("SELECT id, title, original_title, release_year, tmdb_id, poster_url FROM movies ORDER BY id"))).fetchall()
        print(f"Total Movies: {len(movies)}")
        for m in movies:
            print(f"[{m.id:3d}] '{m.title}' | orig='{m.original_title}' | tmdb={m.tmdb_id} | year={m.release_year}")

if __name__ == "__main__":
    asyncio.run(main())
