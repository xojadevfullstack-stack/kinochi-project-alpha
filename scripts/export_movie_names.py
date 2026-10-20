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
        movies = (await conn.execute(text("SELECT id, title, original_title, release_year, tmdb_id FROM movies ORDER BY id"))).fetchall()
        for m in movies:
            print(f"{m.id}|{m.title}|{m.original_title}|{m.release_year}|{m.tmdb_id}")

if __name__ == "__main__":
    asyncio.run(main())
