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

TMDB_API_KEY = settings.TMDB_API_KEY.strip()
HEADERS = {
    "Authorization": f"Bearer {TMDB_API_KEY}",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0"
}

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async with httpx.AsyncClient(headers=HEADERS, timeout=8.0) as client:
        async with engine.connect() as conn:
            movies = (await conn.execute(text("SELECT id, title, original_title, tmdb_id, release_year, poster_url FROM movies ORDER BY id"))).fetchall()
            print(f"Total movies in DB: {len(movies)}")
            
            mismatches = []
            for m in movies:
                tmdb_title = "NONE"
                tmdb_year = "NONE"
                if m.tmdb_id:
                    try:
                        r = await client.get(f"https://api.themoviedb.org/3/movie/{m.tmdb_id}")
                        if r.status_code == 200:
                            data = r.json()
                            tmdb_title = data.get("title") or data.get("original_title")
                            rd = data.get("release_date") or ""
                            tmdb_year = rd[:4] if len(rd) >= 4 else ""
                        else:
                            tmdb_title = f"HTTP_{r.status_code}"
                    except Exception as e:
                        tmdb_title = f"ERR_{e}"

                print(f"[{m.id:3d}] DB: '{m.title}' ({m.release_year}) | TMDB_ID={m.tmdb_id} -> TMDB: '{tmdb_title}' ({tmdb_year})")

if __name__ == "__main__":
    asyncio.run(main())
