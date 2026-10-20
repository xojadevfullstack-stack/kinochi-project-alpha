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
        series = (await conn.execute(text("SELECT id, title, tmdb_id, poster_url FROM series ORDER BY id"))).fetchall()
        print("=== ALL 6 SERIES ===")
        for s in series:
            print(f"[{s.id}] {s.title} | TMDB={s.tmdb_id} | Poster={s.poster_url}")

        seasons = (await conn.execute(text("SELECT id, series_id, season_number, poster_url FROM seasons ORDER BY series_id, season_number"))).fetchall()
        print(f"\n=== ALL {len(seasons)} SEASONS ===")
        for sea in seasons:
            print(f"Season {sea.id} (Series {sea.series_id} S{sea.season_number}): {sea.poster_url}")

if __name__ == "__main__":
    asyncio.run(main())
