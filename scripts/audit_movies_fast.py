import os
import sys
import asyncio
import httpx
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))

from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text

token = os.getenv("TMDB_API_KEY")

async def check_movie(client, sem, m):
    m_id, title, tmdb_id, poster = m
    if not tmdb_id:
        return f"[NO TMDB ID] ID: {m_id} | Title: {title}"
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    headers = {"Authorization": f"Bearer {token}"}
    async with sem:
        try:
            r = await client.get(url, headers=headers, timeout=10.0)
            if r.status_code == 200:
                data = r.json()
                tmdb_title = data.get("title", "")
                orig_title = data.get("original_title", "")
                poster_path = data.get("poster_path")
                # Compare title similarity or inspect
                return {
                    "id": m_id,
                    "title": title,
                    "tmdb_id": tmdb_id,
                    "tmdb_title": tmdb_title,
                    "orig_title": orig_title,
                    "poster": poster,
                    "expected_poster": f"https://image.tmdb.org/t/p/w500{poster_path}" if poster_path else None
                }
            else:
                return f"[HTTP {r.status_code}] ID: {m_id} | {title} | tmdb: {tmdb_id}"
        except Exception as e:
            return f"[ERROR] ID: {m_id} | {title} | tmdb: {tmdb_id}: {e}"

async def main():
    async with async_session_factory() as session:
        res = await session.execute(text("SELECT id, title, tmdb_id, poster_url FROM movies ORDER BY id"))
        movies = res.fetchall()
        print(f"Total movies in DB: {len(movies)}")
        
        sem = asyncio.Semaphore(15)
        async with httpx.AsyncClient() as client:
            tasks = [check_movie(client, sem, m) for m in movies]
            results = await asyncio.gather(*tasks)
            
            for item in results:
                if isinstance(item, str):
                    print(item)
                elif isinstance(item, dict):
                    # check poster difference
                    if item["poster"] != item["expected_poster"]:
                        print(f"[POSTER DIFF] ID: {item['id']} | DB: {item['title']} | TMDb: {item['tmdb_title']} | DB poster: {item['poster']} | TMDb poster: {item['expected_poster']}")

if __name__ == "__main__":
    asyncio.run(main())
