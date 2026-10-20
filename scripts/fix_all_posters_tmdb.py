import asyncio
import os
import sys
import json
import httpx
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))

from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.cache import delete_cache_pattern

TMDB_API_KEY = settings.TMDB_API_KEY.strip()
if TMDB_API_KEY.startswith("ey") or len(TMDB_API_KEY) > 50:
    TMDB_HEADERS = {
        "Authorization": f"Bearer {TMDB_API_KEY}",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    TMDB_PARAMS = {}
else:
    TMDB_HEADERS = {
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    TMDB_PARAMS = {"api_key": TMDB_API_KEY}

IMAGE_HEADERS = {"User-Agent": "Mozilla/5.0"}

# Load pre-verified posters cache
PRE_VERIFIED = {}
if os.path.exists("batch2_real_posters.json"):
    try:
        with open("batch2_real_posters.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            PRE_VERIFIED = {int(k): v for k, v in data.items()}
    except Exception as e:
        print(f"Notice loading batch2_real_posters: {e}")

# Special manual overrides
PRE_VERIFIED[479144] = "https://image.tmdb.org/t/p/w500/9ySkFLATDGH6ML0AA87QldiGQyB.jpg"  # Kurtlar Vadisi Vatan
PRE_VERIFIED[469469] = "https://image.tmdb.org/t/p/w500/9ySkFLATDGH6ML0AA87QldiGQyB.jpg"

async def check_image_url(client: httpx.AsyncClient, url: str) -> bool:
    if not url:
        return False
    try:
        r = await client.head(url, headers=IMAGE_HEADERS, timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False

async def fetch_tmdb_movie_poster(client: httpx.AsyncClient, tmdb_id: int):
    if tmdb_id in PRE_VERIFIED:
        return PRE_VERIFIED[tmdb_id]

    for lang in ["ru-RU", "en-US"]:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
        p = {**TMDB_PARAMS, "language": lang}
        try:
            r = await client.get(url, headers=TMDB_HEADERS, params=p, timeout=7.0)
            if r.status_code == 200:
                ppath = r.json().get("poster_path")
                if ppath:
                    poster_url = f"https://image.tmdb.org/t/p/w500{ppath}"
                    if await check_image_url(client, poster_url):
                        return poster_url
        except Exception:
            pass

    # Try images endpoint
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/images"
        r = await client.get(url, headers=TMDB_HEADERS, params=TMDB_PARAMS, timeout=7.0)
        if r.status_code == 200:
            for p in r.json().get("posters", []):
                ppath = p.get("file_path")
                if ppath:
                    poster_url = f"https://image.tmdb.org/t/p/w500{ppath}"
                    if await check_image_url(client, poster_url):
                        return poster_url
    except Exception:
        pass

    return None

async def fetch_tmdb_tv_poster(client: httpx.AsyncClient, tv_id: int):
    for lang in ["ru-RU", "en-US"]:
        url = f"https://api.themoviedb.org/3/tv/{tv_id}"
        p = {**TMDB_PARAMS, "language": lang}
        try:
            r = await client.get(url, headers=TMDB_HEADERS, params=p, timeout=7.0)
            if r.status_code == 200:
                ppath = r.json().get("poster_path")
                if ppath:
                    poster_url = f"https://image.tmdb.org/t/p/w500{ppath}"
                    if await check_image_url(client, poster_url):
                        return poster_url
        except Exception:
            pass
    return None

async def fetch_tmdb_season_poster(client: httpx.AsyncClient, tv_id: int, season_number: int):
    for lang in ["ru-RU", "en-US"]:
        url = f"https://api.themoviedb.org/3/tv/{tv_id}/season/{season_number}"
        p = {**TMDB_PARAMS, "language": lang}
        try:
            r = await client.get(url, headers=TMDB_HEADERS, params=p, timeout=7.0)
            if r.status_code == 200:
                ppath = r.json().get("poster_path")
                if ppath:
                    poster_url = f"https://image.tmdb.org/t/p/w500{ppath}"
                    if await check_image_url(client, poster_url):
                        return poster_url
        except Exception:
            pass
    return None

async def run_single_pass():
    engine = create_async_engine(settings.DATABASE_URL)
    limits = httpx.Limits(max_keepalive_connections=30, max_connections=40)
    
    async with httpx.AsyncClient(limits=limits) as client:
        # Check and update Series & Seasons
        print("Checking Series...")
        async with engine.begin() as conn:
            series_rows = (await conn.execute(text("SELECT id, title, tmdb_id, poster_url FROM series ORDER BY id"))).fetchall()
            series_posters = {}
            for s in series_rows:
                is_valid = await check_image_url(client, s.poster_url)
                if not is_valid:
                    new_poster = await fetch_tmdb_tv_poster(client, s.tmdb_id)
                    if new_poster:
                        await conn.execute(text("UPDATE series SET poster_url = :url, updated_at = NOW() WHERE id = :id"), {"url": new_poster, "id": s.id})
                        series_posters[s.id] = new_poster
                        print(f"  [SERIES UPDATED] {s.id} {s.title} -> {new_poster}")
                    else:
                        print(f"  [SERIES FAIL] {s.id} {s.title}")
                else:
                    series_posters[s.id] = s.poster_url

            # Seasons
            seasons_rows = (await conn.execute(text("SELECT id, series_id, season_number, poster_url FROM seasons ORDER BY series_id, season_number"))).fetchall()
            series_tmdb_map = {s.id: s.tmdb_id for s in series_rows}
            for sea in seasons_rows:
                is_valid = await check_image_url(client, sea.poster_url)
                if not is_valid:
                    tv_id = series_tmdb_map.get(sea.series_id)
                    new_sea_poster = None
                    if tv_id:
                        new_sea_poster = await fetch_tmdb_season_poster(client, tv_id, sea.season_number)
                    if not new_sea_poster:
                        new_sea_poster = series_posters.get(sea.series_id)
                    
                    if new_sea_poster:
                        await conn.execute(text("UPDATE seasons SET poster_url = :url WHERE id = :id"), {"url": new_sea_poster, "id": sea.id})
                        print(f"  [SEASON UPDATED] Season {sea.id} (Series {sea.series_id} S{sea.season_number}) -> {new_sea_poster}")
                    else:
                        print(f"  [SEASON FAIL] Season {sea.id}")

            # Movies
            movies_rows = (await conn.execute(text("SELECT id, title, original_title, tmdb_id, release_year, poster_url FROM movies ORDER BY id"))).fetchall()
            print(f"Checking {len(movies_rows)} Movies...")
            updated_m = 0
            for m in movies_rows:
                is_valid = await check_image_url(client, m.poster_url)
                if not is_valid:
                    new_poster = None
                    if m.tmdb_id:
                        new_poster = await fetch_tmdb_movie_poster(client, m.tmdb_id)
                    
                    if not new_poster:
                        # Fallback search by title or original_title
                        q = m.original_title or m.title
                        url = "https://api.themoviedb.org/3/search/movie"
                        for lang in ["ru-RU", "en-US"]:
                            p = {**TMDB_PARAMS, "query": q, "language": lang}
                            if m.release_year:
                                p["year"] = m.release_year
                            try:
                                r = await client.get(url, headers=TMDB_HEADERS, params=p, timeout=7.0)
                                if r.status_code == 200:
                                    for item in r.json().get("results", []):
                                        ppath = item.get("poster_path")
                                        if ppath:
                                            cand = f"https://image.tmdb.org/t/p/w500{ppath}"
                                            if await check_image_url(client, cand):
                                                new_poster = cand
                                                break
                            except Exception:
                                pass
                            if new_poster:
                                break

                    if new_poster:
                        await conn.execute(text("UPDATE movies SET poster_url = :url, updated_at = NOW() WHERE id = :id"), {"url": new_poster, "id": m.id})
                        updated_m += 1
                        print(f"  [MOVIE UPDATED] {m.id} {m.title} -> {new_poster}")
                    else:
                        print(f"  [MOVIE FAIL] {m.id} {m.title} (tmdb={m.tmdb_id})")

            print(f"Pass complete: {updated_m} movies updated.")

        # Invalidate Cache
        await delete_cache_pattern("cache:*")
        await delete_cache_pattern("recommendations:*")
        await delete_cache_pattern("*")

if __name__ == "__main__":
    asyncio.run(run_single_pass())
