import asyncio
import os
import sys
import httpx
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
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

async def check_image_url(client: httpx.AsyncClient, url: str) -> bool:
    if not url:
        return False
    try:
        r = await client.head(url, headers=IMAGE_HEADERS, timeout=5.0)
        return r.status_code == 200
    except Exception:
        return False

async def get_tmdb_movie_poster(client: httpx.AsyncClient, tmdb_id: int):
    # Try ru-RU first, then en-US
    for lang in ["ru-RU", "en-US"]:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
        p = {**TMDB_PARAMS, "language": lang}
        try:
            r = await client.get(url, headers=TMDB_HEADERS, params=p, timeout=7.0)
            if r.status_code == 200:
                data = r.json()
                ppath = data.get("poster_path")
                if ppath:
                    poster_url = f"https://image.tmdb.org/t/p/w500{ppath}"
                    if await check_image_url(client, poster_url):
                        return poster_url
        except Exception as e:
            print(f"Error fetching movie {tmdb_id} {lang}: {e}")

    # Fallback to images endpoint
    try:
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/images"
        r = await client.get(url, headers=TMDB_HEADERS, params=TMDB_PARAMS, timeout=7.0)
        if r.status_code == 200:
            for item in r.json().get("posters", []):
                ppath = item.get("file_path")
                if ppath:
                    poster_url = f"https://image.tmdb.org/t/p/w500{ppath}"
                    if await check_image_url(client, poster_url):
                        return poster_url
    except Exception as e:
        print(f"Error fetching movie images {tmdb_id}: {e}")

    return None

async def get_tmdb_tv_poster(client: httpx.AsyncClient, tv_id: int):
    for lang in ["ru-RU", "en-US"]:
        url = f"https://api.themoviedb.org/3/tv/{tv_id}"
        p = {**TMDB_PARAMS, "language": lang}
        try:
            r = await client.get(url, headers=TMDB_HEADERS, params=p, timeout=7.0)
            if r.status_code == 200:
                data = r.json()
                ppath = data.get("poster_path")
                if ppath:
                    poster_url = f"https://image.tmdb.org/t/p/w500{ppath}"
                    if await check_image_url(client, poster_url):
                        return poster_url
        except Exception as e:
            print(f"Error fetching tv {tv_id} {lang}: {e}")
    return None

async def get_tmdb_season_poster(client: httpx.AsyncClient, tv_id: int, season_number: int):
    for lang in ["ru-RU", "en-US"]:
        url = f"https://api.themoviedb.org/3/tv/{tv_id}/season/{season_number}"
        p = {**TMDB_PARAMS, "language": lang}
        try:
            r = await client.get(url, headers=TMDB_HEADERS, params=p, timeout=7.0)
            if r.status_code == 200:
                data = r.json()
                ppath = data.get("poster_path")
                if ppath:
                    poster_url = f"https://image.tmdb.org/t/p/w500{ppath}"
                    if await check_image_url(client, poster_url):
                        return poster_url
        except Exception as e:
            print(f"Error fetching season {season_number} of tv {tv_id}: {e}")
    return None

async def run_update():
    print("===================================================================")
    print("       STARTING BATCH TMDB POSTER UPDATE (MOVIES/SERIES/SEASONS)   ")
    print("===================================================================")

    engine = create_async_engine(settings.DATABASE_URL)
    limits = httpx.Limits(max_keepalive_connections=30, max_connections=40)
    
    async with httpx.AsyncClient(limits=limits) as client:
        async with engine.begin() as conn:
            # 1. Update Series
            print("\n>>> 1. Processing Series...")
            series_rows = (await conn.execute(text("SELECT id, title, tmdb_id, poster_url FROM series ORDER BY id"))).fetchall()
            series_poster_cache = {}
            for s in series_rows:
                poster = await get_tmdb_tv_poster(client, s.tmdb_id)
                if poster:
                    series_poster_cache[s.id] = poster
                    await conn.execute(text("UPDATE series SET poster_url = :url, updated_at = NOW() WHERE id = :id"), {"url": poster, "id": s.id})
                    print(f"  [SERIES {s.id}] {s.title} -> {poster}")
                else:
                    print(f"  [SERIES {s.id}] WARN: Could not find poster for {s.title}")

            # 2. Update Seasons
            print("\n>>> 2. Processing Seasons...")
            seasons_rows = (await conn.execute(text("SELECT id, series_id, season_number, poster_url FROM seasons ORDER BY series_id, season_number"))).fetchall()
            # Also get series tmdb_id map
            series_tmdb_map = {s.id: s.tmdb_id for s in series_rows}
            for sea in seasons_rows:
                tv_id = series_tmdb_map.get(sea.series_id)
                sea_poster = None
                if tv_id:
                    sea_poster = await get_tmdb_season_poster(client, tv_id, sea.season_number)
                if not sea_poster:
                    sea_poster = series_poster_cache.get(sea.series_id)
                
                if sea_poster:
                    await conn.execute(text("UPDATE seasons SET poster_url = :url WHERE id = :id"), {"url": sea_poster, "id": sea.id})
                    print(f"  [SEASON {sea.id}] (Series {sea.series_id} S{sea.season_number}) -> {sea_poster}")
                else:
                    print(f"  [SEASON {sea.id}] WARN: No poster for season {sea.season_number}")

            # 3. Update Movies
            print("\n>>> 3. Processing Movies...")
            movies_rows = (await conn.execute(text("SELECT id, title, original_title, tmdb_id, poster_url FROM movies ORDER BY id"))).fetchall()
            m_success = 0
            for m in movies_rows:
                m_poster = None
                if m.tmdb_id:
                    m_poster = await get_tmdb_movie_poster(client, m.tmdb_id)
                
                if m_poster:
                    await conn.execute(text("UPDATE movies SET poster_url = :url, updated_at = NOW() WHERE id = :id"), {"url": m_poster, "id": m.id})
                    m_success += 1
                    print(f"  [MOVIE {m.id}] {m.title} -> {m_poster}")
                else:
                    print(f"  [MOVIE {m.id}] FAIL: No poster found for {m.title} (tmdb_id={m.tmdb_id})")

            print(f"\nSuccessfully updated {m_success}/{len(movies_rows)} movies!")

    # 4. Clear Cache
    print("\n>>> 4. Flushing cache...")
    try:
        await delete_cache_pattern("cache:*")
        await delete_cache_pattern("recommendations:*")
        await delete_cache_pattern("*")
        print("Caches cleared successfully!")
    except Exception as e:
        print(f"Cache notice: {e}")

    # 5. Final HTTP Audit
    print("\n>>> 5. Running Full HTTP Verification Audit...")
    async with httpx.AsyncClient(limits=limits) as client:
        async with engine.connect() as conn:
            movies = (await conn.execute(text("SELECT id, title, poster_url FROM movies ORDER BY id"))).fetchall()
            m_ok = 0
            m_bad = 0
            for m in movies:
                if await check_image_url(client, m.poster_url):
                    m_ok += 1
                else:
                    m_bad += 1
                    print(f"  FAILED MOVIE: [{m.id}] {m.title}: {m.poster_url}")

            series = (await conn.execute(text("SELECT id, title, poster_url FROM series ORDER BY id"))).fetchall()
            s_ok = 0
            s_bad = 0
            for s in series:
                if await check_image_url(client, s.poster_url):
                    s_ok += 1
                else:
                    s_bad += 1
                    print(f"  FAILED SERIES: [{s.id}] {s.title}: {s.poster_url}")

            seasons = (await conn.execute(text("SELECT id, series_id, season_number, poster_url FROM seasons ORDER BY id"))).fetchall()
            sea_ok = 0
            sea_bad = 0
            for sea in seasons:
                if await check_image_url(client, sea.poster_url):
                    sea_ok += 1
                else:
                    sea_bad += 1
                    print(f"  FAILED SEASON: [{sea.id}] Series {sea.series_id} S{sea.season_number}: {sea.poster_url}")

    print("\n===================================================================")
    print("                    FINAL AUDIT RESULTS                            ")
    print(f"  Movies : {m_ok}/{len(movies)} ({m_ok/len(movies)*100:.1f}%) HTTP 200 VALID POSTERS (Broken: {m_bad})")
    print(f"  Series : {s_ok}/{len(series)} ({s_ok/len(series)*100:.1f}%) HTTP 200 VALID POSTERS (Broken: {s_bad})")
    print(f"  Seasons: {sea_ok}/{len(seasons)} ({sea_ok/len(seasons)*100:.1f}%) HTTP 200 VALID POSTERS (Broken: {sea_bad})")
    print("===================================================================")

if __name__ == "__main__":
    asyncio.run(run_update())
