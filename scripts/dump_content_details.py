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
            print(f"ID={m.id:3d} | TMDB_ID={str(m.tmdb_id):8s} | Year={str(m.release_year):4s} | Title='{m.title}' | Orig='{m.original_title}' | Poster={m.poster_url}")

        series = (await conn.execute(text("SELECT id, title, release_year, tmdb_id, poster_url FROM series ORDER BY id"))).fetchall()
        print(f"\nTotal Series: {len(series)}")
        for s in series:
            print(f"ID={s.id:3d} | TMDB_ID={str(s.tmdb_id):8s} | Year={str(s.release_year):4s} | Title='{s.title}' | Poster={s.poster_url}")

if __name__ == "__main__":
    asyncio.run(main())
