import asyncio
import os
import sys
import httpx
import urllib.parse
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))

from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

TMDB_API_KEY = settings.TMDB_API_KEY
HEADERS = {
    "Authorization": f"Bearer {TMDB_API_KEY}" if (TMDB_API_KEY.startswith("ey") or len(TMDB_API_KEY) > 50) else None,
    "Accept": "application/json"
}
PARAMS = {} if HEADERS.get("Authorization") else {"api_key": TMDB_API_KEY}

async def fetch_tmdb_movie_poster(client: httpx.AsyncClient, tmdb_id: int):
    # 1. Try ru-RU
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    p = {**PARAMS, "language": "ru-RU"}
    r = await client.get(url, params=p, headers=HEADERS)
    if r.status_code == 200:
        data = r.json()
        ppath = data.get("poster_path")
        if ppath:
            return f"https://image.tmdb.org/t/p/w500{ppath}", data.get("title") or data.get("original_title")

    # 2. Try en-US
    p = {**PARAMS, "language": "en-US"}
    r = await client.get(url, params=p, headers=HEADERS)
    if r.status_code == 200:
        data = r.json()
        ppath = data.get("poster_path")
        if ppath:
            return f"https://image.tmdb.org/t/p/w500{ppath}", data.get("title") or data.get("original_title")

    # 3. Check images endpoint
    url_img = f"https://api.themoviedb.org/3/movie/{tmdb_id}/images"
    r = await client.get(url_img, params=PARAMS, headers=HEADERS)
    if r.status_code == 200:
        posters = r.json().get("posters", [])
        if posters:
            return f"https://image.tmdb.org/t/p/w500{posters[0]['file_path']}", None

    return None, None

async def search_tmdb_movie(client: httpx.AsyncClient, query: str, year: int = None):
    url = "https://api.themoviedb.org/3/search/movie"
    for lang in ["ru-RU", "en-US"]:
        p = {**PARAMS, "query": query, "language": lang}
        if year:
            p["year"] = year
        r = await client.get(url, params=p, headers=HEADERS)
        if r.status_code == 200:
            results = r.json().get("results", [])
            for res in results:
                if res.get("poster_path"):
                    return res["id"], f"https://image.tmdb.org/t/p/w500{res['poster_path']}", res.get("title")
    return None, None, None

async def fetch_tmdb_tv_poster(client: httpx.AsyncClient, tmdb_id: int):
    url = f"https://api.themoviedb.org/3/tv/{tmdb_id}"
    for lang in ["ru-RU", "en-US"]:
        p = {**PARAMS, "language": lang}
        r = await client.get(url, params=p, headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            ppath = data.get("poster_path")
            if ppath:
                return f"https://image.tmdb.org/t/p/w500{ppath}", data.get("name") or data.get("original_name")
    return None, None

async def fetch_tmdb_season_poster(client: httpx.AsyncClient, tv_id: int, season_number: int):
    url = f"https://api.themoviedb.org/3/tv/{tv_id}/season/{season_number}"
    for lang in ["ru-RU", "en-US"]:
        p = {**PARAMS, "language": lang}
        r = await client.get(url, params=p, headers=HEADERS)
        if r.status_code == 200:
            data = r.json()
            ppath = data.get("poster_path")
            if ppath:
                return f"https://image.tmdb.org/t/p/w500{ppath}"
    return None

async def test_dry_run():
    engine = create_async_engine(settings.DATABASE_URL)
    async with httpx.AsyncClient(timeout=10.0) as client:
        async with engine.connect() as conn:
            movies = (await conn.execute(text("SELECT id, title, original_title, release_year, tmdb_id, poster_url FROM movies ORDER BY id"))).fetchall()
            print(f"=== TESTING DRY RUN FOR {len(movies)} MOVIES ===")
            resolved = 0
            unresolved = []
            for m in movies:
                poster = None
                matched_title = None
                new_tmdb_id = m.tmdb_id

                if m.tmdb_id:
                    poster, matched_title = await fetch_tmdb_movie_poster(client, m.tmdb_id)

                if not poster and m.original_title:
                    new_tmdb_id, poster, matched_title = await search_tmdb_movie(client, m.original_title, m.release_year)

                if not poster:
                    new_tmdb_id, poster, matched_title = await search_tmdb_movie(client, m.title, m.release_year)

                if poster:
                    # verify HTTP 200
                    h = await client.head(poster)
                    if h.status_code == 200:
                        resolved += 1
                        print(f"OK [{m.id}] {m.title} -> {poster}")
                    else:
                        print(f"HEAD FAIL [{m.id}] {m.title} -> {poster} returned {h.status_code}")
                        unresolved.append(m)
                else:
                    print(f"NOT FOUND [{m.id}] {m.title} (orig={m.original_title}, tmdb={m.tmdb_id})")
                    unresolved.append(m)

            print(f"\nMovies Dry Run: {resolved}/{len(movies)} resolved successfully!")
            if unresolved:
                print(f"Unresolved movies: {[m.title for m in unresolved]}")

            series = (await conn.execute(text("SELECT id, title, release_year, tmdb_id, poster_url FROM series ORDER BY id"))).fetchall()
            print(f"\n=== TESTING DRY RUN FOR {len(series)} SERIES ===")
            s_resolved = 0
            for s in series:
                poster = None
                if s.tmdb_id:
                    poster, _ = await fetch_tmdb_tv_poster(client, s.tmdb_id)
                if poster:
                    h = await client.head(poster)
                    if h.status_code == 200:
                        s_resolved += 1
                        print(f"OK Series [{s.id}] {s.title} -> {poster}")
                    else:
                        print(f"HEAD FAIL Series [{s.id}] {s.title} -> {poster}")
                else:
                    print(f"NOT FOUND Series [{s.id}] {s.title}")
            print(f"Series Dry Run: {s_resolved}/{len(series)} resolved successfully!")

if __name__ == "__main__":
    asyncio.run(test_dry_run())
