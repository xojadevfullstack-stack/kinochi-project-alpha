import asyncio
import os
import sys
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_url(client, url):
    if not url:
        return False, "EMPTY"
    try:
        r = await client.head(url, timeout=5.0)
        if r.status_code == 200:
            return True, "200"
        return False, str(r.status_code)
    except Exception as e:
        return False, f"ERR:{type(e).__name__}"

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async with httpx.AsyncClient(headers={"User-Agent": "Mozilla/5.0"}) as client:
        async with engine.connect() as conn:
            # Check Movies
            movies = (await conn.execute(text("SELECT id, title, original_title, release_year, tmdb_id, poster_url FROM movies ORDER BY id"))).fetchall()
            print(f"=== CHECKING {len(movies)} MOVIES ===")
            m_valid = 0
            m_broken = 0
            broken_movies = []
            for m in movies:
                valid, status = await check_url(client, m.poster_url)
                if valid:
                    m_valid += 1
                else:
                    m_broken += 1
                    broken_movies.append((m, status))
            print(f"Movies: Valid posters={m_valid}, Broken/Empty posters={m_broken}")
            for m, st in broken_movies[:10]:
                print(f"  Broken [{m.id}] {m.title} ({m.release_year}): status={st}, url={m.poster_url}, tmdb_id={m.tmdb_id}")

            # Check Series
            series = (await conn.execute(text("SELECT id, title, release_year, tmdb_id, poster_url FROM series ORDER BY id"))).fetchall()
            print(f"\n=== CHECKING {len(series)} SERIES ===")
            s_valid = 0
            s_broken = 0
            broken_series = []
            for s in series:
                valid, status = await check_url(client, s.poster_url)
                if valid:
                    s_valid += 1
                else:
                    s_broken += 1
                    broken_series.append((s, status))
            print(f"Series: Valid posters={s_valid}, Broken/Empty posters={s_broken}")
            for s, st in broken_series:
                print(f"  Broken [{s.id}] {s.title} ({s.release_year}): status={st}, url={s.poster_url}, tmdb_id={s.tmdb_id}")

            # Check Seasons
            seasons = (await conn.execute(text("SELECT id, series_id, season_number, poster_url FROM seasons ORDER BY id"))).fetchall()
            print(f"\n=== CHECKING {len(seasons)} SEASONS ===")
            sea_valid = 0
            sea_broken = 0
            for sea in seasons:
                valid, status = await check_url(client, sea.poster_url)
                if valid:
                    sea_valid += 1
                else:
                    sea_broken += 1
            print(f"Seasons: Valid posters={sea_valid}, Broken/Empty posters={sea_broken}")

            # Check Collections
            collections = (await conn.execute(text("SELECT id, title, poster_url FROM collections ORDER BY id"))).fetchall()
            print(f"\n=== CHECKING {len(collections)} COLLECTIONS ===")
            c_valid = 0
            c_broken = 0
            for c in collections:
                valid, status = await check_url(client, c.poster_url)
                if valid:
                    c_valid += 1
                else:
                    c_broken += 1
            print(f"Collections: Valid posters={c_valid}, Broken/Empty posters={c_broken}")

if __name__ == "__main__":
    asyncio.run(main())
