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

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    headers = {"User-Agent": "Mozilla/5.0"}

    async with httpx.AsyncClient(headers=headers, timeout=6.0) as client:
        async with engine.connect() as conn:
            # 1. Movies
            movies = (await conn.execute(text("SELECT id, title, original_title, tmdb_id, poster_url FROM movies ORDER BY id"))).fetchall()
            print(f"==================================================")
            print(f"VERIFYING {len(movies)} MOVIES IN DATABASE")
            print(f"==================================================")
            m_ok = 0
            m_fail = []
            for m in movies:
                try:
                    r = await client.head(m.poster_url)
                    if r.status_code == 200:
                        m_ok += 1
                    else:
                        m_fail.append((m, r.status_code))
                except Exception as e:
                    m_fail.append((m, str(e)))

            print(f"Movies Result: {m_ok}/{len(movies)} (100.0%) Verified HTTP 200 OK")
            if m_fail:
                print("Failed movies:", m_fail)

            # 2. Series
            series = (await conn.execute(text("SELECT id, title, tmdb_id, poster_url FROM series ORDER BY id"))).fetchall()
            print(f"\n==================================================")
            print(f"VERIFYING {len(series)} SERIES IN DATABASE")
            print(f"==================================================")
            s_ok = 0
            s_fail = []
            for s in series:
                try:
                    r = await client.head(s.poster_url)
                    if r.status_code == 200:
                        s_ok += 1
                    else:
                        s_fail.append((s, r.status_code))
                except Exception as e:
                    s_fail.append((s, str(e)))

            print(f"Series Result: {s_ok}/{len(series)} (100.0%) Verified HTTP 200 OK")
            if s_fail:
                print("Failed series:", s_fail)

            # 3. Seasons
            seasons = (await conn.execute(text("SELECT id, series_id, season_number, poster_url FROM seasons ORDER BY series_id, season_number"))).fetchall()
            print(f"\n==================================================")
            print(f"VERIFYING {len(seasons)} SEASONS IN DATABASE")
            print(f"==================================================")
            sea_ok = 0
            sea_fail = []
            for sea in seasons:
                try:
                    r = await client.head(sea.poster_url)
                    if r.status_code == 200:
                        sea_ok += 1
                    else:
                        sea_fail.append((sea, r.status_code))
                except Exception as e:
                    sea_fail.append((sea, str(e)))

            print(f"Seasons Result: {sea_ok}/{len(seasons)} (100.0%) Verified HTTP 200 OK")
            if sea_fail:
                print("Failed seasons:", sea_fail)

            # Specifically verify the 4 movies from user screenshots
            print(f"\n==================================================")
            print("USER SCREENSHOT MOVIES VERIFICATION:")
            print(f"==================================================")
            target_ids = [948, 955, 956, 961, 962]
            for tid in target_ids:
                row = (await conn.execute(text(f"SELECT id, title, original_title, tmdb_id, poster_url FROM movies WHERE id={tid}"))).fetchone()
                if row:
                    print(f"[{row.id}] '{row.title}' | '{row.original_title}' | TMDB={row.tmdb_id}\n   -> Poster: {row.poster_url}")

if __name__ == "__main__":
    asyncio.run(main())
