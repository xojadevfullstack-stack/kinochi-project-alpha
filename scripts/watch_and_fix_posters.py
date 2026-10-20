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

PRE_VERIFIED = {}
if os.path.exists("batch2_real_posters.json"):
    try:
        with open("batch2_real_posters.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            PRE_VERIFIED = {int(k): v for k, v in data.items()}
    except Exception:
        pass

PRE_VERIFIED[479144] = "https://image.tmdb.org/t/p/w500/9ySkFLATDGH6ML0AA87QldiGQyB.jpg"
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

import subprocess

async def wait_for_process(pid=6448):
    print(f"Checking if process {pid} is running...")
    while True:
        try:
            out = subprocess.check_output(f'tasklist /FI "PID eq {pid}"', shell=True).decode("cp1251", errors="ignore")
            if str(pid) in out:
                print(f"Process {pid} is still actively migrating movies. Waiting 10s...")
                await asyncio.sleep(10)
            else:
                print(f"Process {pid} has completed!")
                break
        except Exception as e:
            print(f"Process check note: {e}")
            break

async def fix_all():
    # First, wait for batch2 migration process to finish
    await wait_for_process(6448)

    print("\n>>> ALL MIGRATION PROCESSES FINISHED. RUNNING DEFINITIVE POSTER FIX...")
    engine = create_async_engine(settings.DATABASE_URL)
    limits = httpx.Limits(max_keepalive_connections=30, max_connections=40)

    async with httpx.AsyncClient(limits=limits) as client:
        async with engine.begin() as conn:
            # 1. Update Series
            series_rows = (await conn.execute(text("SELECT id, title, tmdb_id, poster_url FROM series ORDER BY id"))).fetchall()
            series_posters = {}
            for s in series_rows:
                is_valid = await check_image_url(client, s.poster_url)
                if not is_valid:
                    # fetch tv poster
                    url = f"https://api.themoviedb.org/3/tv/{s.tmdb_id}"
                    new_poster = None
                    for lang in ["ru-RU", "en-US"]:
                        p = {**TMDB_PARAMS, "language": lang}
                        r = await client.get(url, headers=TMDB_HEADERS, params=p)
                        if r.status_code == 200:
                            ppath = r.json().get("poster_path")
                            if ppath:
                                new_poster = f"https://image.tmdb.org/t/p/w500{ppath}"
                                break
                    if new_poster:
                        await conn.execute(text("UPDATE series SET poster_url = :url, updated_at = NOW() WHERE id = :id"), {"url": new_poster, "id": s.id})
                        series_posters[s.id] = new_poster
                        print(f"  [SERIES FIX] {s.id} {s.title} -> {new_poster}")
                else:
                    series_posters[s.id] = s.poster_url

            # 2. Update Seasons
            seasons_rows = (await conn.execute(text("SELECT id, series_id, season_number, poster_url FROM seasons ORDER BY series_id, season_number"))).fetchall()
            series_tmdb_map = {s.id: s.tmdb_id for s in series_rows}
            for sea in seasons_rows:
                is_valid = await check_image_url(client, sea.poster_url)
                if not is_valid:
                    tv_id = series_tmdb_map.get(sea.series_id)
                    new_sea = None
                    if tv_id:
                        url = f"https://api.themoviedb.org/3/tv/{tv_id}/season/{sea.season_number}"
                        for lang in ["ru-RU", "en-US"]:
                            r = await client.get(url, headers=TMDB_HEADERS, params={**TMDB_PARAMS, "language": lang})
                            if r.status_code == 200:
                                ppath = r.json().get("poster_path")
                                if ppath:
                                    new_sea = f"https://image.tmdb.org/t/p/w500{ppath}"
                                    break
                    if not new_sea:
                        new_sea = series_posters.get(sea.series_id)
                    if new_sea:
                        await conn.execute(text("UPDATE seasons SET poster_url = :url WHERE id = :id"), {"url": new_sea, "id": sea.id})
                        print(f"  [SEASON FIX] Season {sea.id} (Series {sea.series_id} S{sea.season_number}) -> {new_sea}")

            # 3. Update Movies
            movies_rows = (await conn.execute(text("SELECT id, title, original_title, tmdb_id, release_year, poster_url FROM movies ORDER BY id"))).fetchall()
            print(f"Auditing all {len(movies_rows)} Movies...")
            fixed_count = 0
            for m in movies_rows:
                is_valid = await check_image_url(client, m.poster_url)
                if not is_valid:
                    new_poster = None
                    if m.tmdb_id:
                        new_poster = await fetch_tmdb_movie_poster(client, m.tmdb_id)
                    
                    if not new_poster:
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
                        fixed_count += 1
                        print(f"  [MOVIE FIX] {m.id} '{m.title}' -> {new_poster}")
                    else:
                        print(f"  [MOVIE ERROR] Cannot resolve poster for {m.id} '{m.title}'")

            print(f"\nFixed {fixed_count} movies with broken posters!")

        # 4. Clear all caches
        print("\n>>> Flushing cache...")
        await delete_cache_pattern("cache:*")
        await delete_cache_pattern("recommendations:*")
        await delete_cache_pattern("*")
        print("All caches cleared!")

        # 5. Full HTTP Audit
        print("\n>>> Running 100% Comprehensive HTTP Audit...")
        async with engine.connect() as conn:
            movies = (await conn.execute(text("SELECT id, title, poster_url FROM movies ORDER BY id"))).fetchall()
            m_ok, m_bad = 0, 0
            for m in movies:
                if await check_image_url(client, m.poster_url):
                    m_ok += 1
                else:
                    m_bad += 1
                    print(f"  FAIL MOVIE: {m.id} {m.title}: {m.poster_url}")

            series = (await conn.execute(text("SELECT id, title, poster_url FROM series ORDER BY id"))).fetchall()
            s_ok, s_bad = 0, 0
            for s in series:
                if await check_image_url(client, s.poster_url):
                    s_ok += 1
                else:
                    s_bad += 1
                    print(f"  FAIL SERIES: {s.id} {s.title}: {s.poster_url}")

            seasons = (await conn.execute(text("SELECT id, series_id, season_number, poster_url FROM seasons ORDER BY id"))).fetchall()
            sea_ok, sea_bad = 0, 0
            for sea in seasons:
                if await check_image_url(client, sea.poster_url):
                    sea_ok += 1
                else:
                    sea_bad += 1
                    print(f"  FAIL SEASON: {sea.id} (Series {sea.series_id} S{sea.season_number}): {sea.poster_url}")

    print("\n===================================================================")
    print("                    FINAL AUDIT RESULTS                            ")
    print(f"  Movies : {m_ok}/{len(movies)} ({m_ok/len(movies)*100:.1f}%) HTTP 200 VALID POSTERS (Broken: {m_bad})")
    print(f"  Series : {s_ok}/{len(series)} ({s_ok/len(series)*100:.1f}%) HTTP 200 VALID POSTERS (Broken: {s_bad})")
    print(f"  Seasons: {sea_ok}/{len(seasons)} ({sea_ok/len(seasons)*100:.1f}%) HTTP 200 VALID POSTERS (Broken: {sea_bad})")
    print("===================================================================")

if __name__ == "__main__":
    asyncio.run(fix_all())
