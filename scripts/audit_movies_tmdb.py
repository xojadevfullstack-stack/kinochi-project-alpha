import os
import sys
import json
import urllib.request
import asyncio
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))

from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text

token = os.getenv("TMDB_API_KEY")

async def main():
    async with async_session_factory() as session:
        res = await session.execute(text("SELECT id, title, tmdb_id, poster_url FROM movies ORDER BY id"))
        movies = res.fetchall()
        print(f"Total movies in DB: {len(movies)}")
        
        mismatches = []
        for m in movies:
            m_id, title, tmdb_id, poster = m
            if not tmdb_id:
                print(f"[NO TMDB ID] {m_id}: {title}")
                continue
            try:
                url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
                req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
                with urllib.request.urlopen(req) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    tmdb_title = data.get("title", "")
                    orig_title = data.get("original_title", "")
                    # Log if suspicious
                    # Compare simple lowered tokens
                    t_lower = title.lower()
                    tmdb_lower = tmdb_title.lower()
                    orig_lower = orig_title.lower()
                    # print sample or check
            except Exception as e:
                print(f"[ERROR TMDB] {m_id} {title} (tmdb: {tmdb_id}): {e}")

asyncio.run(main())
