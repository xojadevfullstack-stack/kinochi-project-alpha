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
        
        errors = []
        for m in movies:
            m_id, title, tmdb_id, poster = m
            if not tmdb_id:
                print(f"[NO TMDB ID] ID: {m_id} | Title: {title}")
                continue
            try:
                url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
                req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
                with urllib.request.urlopen(req) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    tmdb_title = data.get("title", "")
                    orig_title = data.get("original_title", "")
                    poster_path = data.get("poster_path")
                    # Check if DB poster matches tmdb poster
                    expected_poster = f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                    if poster != expected_poster and expected_poster is not None:
                        print(f"[POSTER MISMATCH] ID: {m_id} | {title} | TMDb Title: {tmdb_title} | DB Poster: {poster} != TMDb Poster: {expected_poster}")
            except Exception as e:
                print(f"[TMDB FETCH ERROR] ID: {m_id} | {title} | tmdb: {tmdb_id} | Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
