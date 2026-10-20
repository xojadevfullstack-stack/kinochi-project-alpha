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
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel, SeasonModel
from app.core.cache import delete_cache_pattern
from sqlalchemy import select

TMDB_API_KEY = settings.TMDB_API_KEY
HEADERS = {
    "Authorization": f"Bearer {TMDB_API_KEY}" if (TMDB_API_KEY.startswith("ey") or len(TMDB_API_KEY) > 50) else None,
    "Accept": "application/json"
}
PARAMS = {} if HEADERS.get("Authorization") else {"api_key": TMDB_API_KEY}

async def check_url_status(client: httpx.AsyncClient, url: str) -> bool:
    if not url:
        return False
    try:
        r = await client.head(url, timeout=6.0)
        return r.status_code == 200
    except Exception:
        return False

async def fetch_movie_poster(client: httpx.AsyncClient, tmdb_id: int):
    url = f"https://api.themoviedb.org/3/movie/{tmdb_id}"
    for lang in ["ru-RU", "en-US"]:
        try:
            r = await client.get(url, params={**PARAMS, "language": lang})
            if r.status_code == 200:
                data = r.json()
                ppath = data.get("poster_path")
                if ppath:
                    full_url = f"https://image.tmdb.org/t/p/w500{ppath}"
                    if await check_url_status(client, full_url):
                        return full_url, data.get("title") or data.get("original_title")
        except Exception as e:
            print(f"Error fetching movie {tmdb_id} lang={lang}: {e}")

    # Fallback to images
    try:
        r = await client.get(f"https://api.themoviedb.org/3/movie/{tmdb_id}/images", params=PARAMS)
        if r.status_code == 200:
            posters = r.json().get("posters", [])
            for p in posters:
                fpath = p.get("file_path")
                if fpath:
                    full_url = f"https://image.tmdb.org/t/p/w500{fpath}"
                    if await check_url_status(client, full_url):
                        return full_url, None
    except Exception as e:
        print(f"Error fetching images for movie {tmdb_id}: {e}")

    return None, None

async def search_movie(client: httpx.AsyncClient, query: str, year: int = None):
    url = "https://api.themoviedb.org/3/search/movie"
    for lang in ["ru-RU", "en-US"]:
        p = {**PARAMS, "query": query, "language": lang}
        if year:
            p["year"] = year
        try:
            r = await client.get(url, params=p)
            if r.status_code == 200:
                for item in r.json().get("results", []):
                    ppath = item.get("poster_path")
                    if ppath:
                        full_url = f"https://image.tmdb.org/t/p/w500{ppath}"
                        if await check_url_status(client, full_url):
                            return item["id"], full_url, item.get("title") or item.get("original_title")
        except Exception as e:
            print(f"Error searching movie '{query}': {e}")
    return None, None, None

async def fetch_tv_poster(client: httpx.AsyncClient, tmdb_id: int):
    url = f"https://api.themoviedb.org/3/tv/{tmdb_id}"
    for lang in ["ru-RU", "en-US"]:
        try:
            r = await client.get(url, params={**PARAMS, "language": lang})
            if r.status_code == 200:
                data = r.json()
                ppath = data.get("poster_path")
                if ppath:
                    full_url = f"https://image.tmdb.org/t/p/w500{ppath}"
                    if await check_url_status(client, full_url):
                        return full_url
        except Exception as e:
            print(f"Error fetching tv {tmdb_id}: {e}")
    return None

async def fetch_season_poster(client: httpx.AsyncClient, tv_id: int, season_number: int):
    url = f"https://api.themoviedb.org/3/tv/{tv_id}/season/{season_number}"
    for lang in ["ru-RU", "en-US"]:
        try:
            r = await client.get(url, params={**PARAMS, "language": lang})
            if r.status_code == 200:
                data = r.json()
                ppath = data.get("poster_path")
                if ppath:
                    full_url = f"https://image.tmdb.org/t/p/w500{ppath}"
                    if await check_url_status(client, full_url):
                        return full_url
        except Exception as e:
            print(f"Error fetching season {season_number} of tv {tv_id}: {e}")
    return None

async def main():
    print("==========================================================")
    print("   STARTING TMDB POSTER UPDATE FOR ALL MOVIES & SERIES   ")
    print("==========================================================")

    limits = httpx.Limits(max_keepalive_connections=20, max_connections=30)
    timeout = httpx.Timeout(12.0, connect=6.0)

    async with httpx.AsyncClient(limits=limits, timeout=timeout, headers={"User-Agent": "Mozilla/5.0"}) as client:
        async with async_session_factory() as session:
            # 1. Update Series & Seasons
            print("\n>>> 1. UPDATING SERIES & SEASONS...")
            stmt_series = select(SeriesModel).order_by(SeriesModel.id)
            series_list = (await session.execute(stmt_series)).scalars().all()
            
            series_poster_map = {}
            for s in series_list:
                s_poster = None
                if s.tmdb_id:
                    s_poster = await fetch_tv_poster(client, s.tmdb_id)
                if not s_poster:
                    # fallback search
                    url = "https://api.themoviedb.org/3/search/tv"
                    for lang in ["ru-RU", "en-US"]:
                        p = {**PARAMS, "query": s.title, "language": lang}
                        r = await client.get(url, params=p)
                        if r.status_code == 200:
                            for item in r.json().get("results", []):
                                ppath = item.get("poster_path")
                                if ppath:
                                    cand = f"https://image.tmdb.org/t/p/w500{ppath}"
                                    if await check_url_status(client, cand):
                                        s_poster = cand
                                        s.tmdb_id = item["id"]
                                        break
                        if s_poster:
                            break

                if s_poster:
                    s.poster_url = s_poster
                    series_poster_map[s.id] = s_poster
                    print(f"  [SERIES {s.id}] '{s.title}' -> Poster: {s_poster}")
                else:
                    print(f"  [SERIES {s.id}] WARN: Poster not found for '{s.title}'")

                # Update seasons for this series
                for sea in s.seasons:
                    sea_poster = None
                    if s.tmdb_id:
                        sea_poster = await fetch_season_poster(client, s.tmdb_id, sea.season_number)
                    if not sea_poster:
                        sea_poster = s_poster  # Fallback to series poster
                    
                    if sea_poster:
                        sea.poster_url = sea_poster
                        print(f"     [SEASON {sea.season_number}] (ID={sea.id}) -> Poster: {sea_poster}")

            # 2. Update Movies
            print("\n>>> 2. UPDATING MOVIES...")
            stmt_movies = select(MovieModel).order_by(MovieModel.id)
            movies_list = (await session.execute(stmt_movies)).scalars().all()

            updated_movies = 0
            for m in movies_list:
                m_poster = None
                orig_title_candidate = None

                # Step A: By existing tmdb_id
                if m.tmdb_id:
                    m_poster, orig_title_candidate = await fetch_movie_poster(client, m.tmdb_id)

                # Step B: By original_title if poster not found
                if not m_poster and m.original_title:
                    new_id, m_poster, orig_title_candidate = await search_movie(client, m.original_title, m.release_year)
                    if new_id and not m.tmdb_id:
                        m.tmdb_id = new_id

                # Step C: By title
                if not m_poster and m.title:
                    new_id, m_poster, orig_title_candidate = await search_movie(client, m.title, m.release_year)
                    if new_id and not m.tmdb_id:
                        m.tmdb_id = new_id

                if m_poster:
                    m.poster_url = m_poster
                    if not m.original_title and orig_title_candidate:
                        m.original_title = orig_title_candidate
                    updated_movies += 1
                    print(f"  [MOVIE {m.id}] '{m.title}' -> Poster: {m_poster}")
                else:
                    print(f"  [MOVIE {m.id}] WARN: Could not resolve poster for '{m.title}' (orig={m.original_title})")

            # Commit to Postgres
            await session.commit()
            print(f"\nSuccessfully committed changes to database! ({updated_movies}/{len(movies_list)} movies updated)")

    # 3. Clear Cache
    print("\n>>> 3. CLEARING CACHE...")
    try:
        await delete_cache_pattern("cache:*")
        await delete_cache_pattern("recommendations:*")
        await delete_cache_pattern("*movie*")
        await delete_cache_pattern("*series*")
        await delete_cache_pattern("*")
        print("All caches invalidated successfully!")
    except Exception as e:
        print(f"Cache clear notice: {e}")

    # 4. Final Verification
    print("\n>>> 4. RUNNING FINAL HTTP VERIFICATION AUDIT...")
    async with httpx.AsyncClient(timeout=8.0, headers={"User-Agent": "Mozilla/5.0"}) as client:
        async with async_session_factory() as session:
            movies = (await session.execute(select(MovieModel).order_by(MovieModel.id))).scalars().all()
            m_ok = 0
            m_bad = 0
            for m in movies:
                if await check_url_status(client, m.poster_url):
                    m_ok += 1
                else:
                    m_bad += 1
                    print(f"  [VERIFY FAIL] Movie {m.id} '{m.title}': {m.poster_url}")

            series = (await session.execute(select(SeriesModel).order_by(SeriesModel.id))).scalars().all()
            s_ok = 0
            s_bad = 0
            for s in series:
                if await check_url_status(client, s.poster_url):
                    s_ok += 1
                else:
                    s_bad += 1
                    print(f"  [VERIFY FAIL] Series {s.id} '{s.title}': {s.poster_url}")

            seasons = (await session.execute(select(SeasonModel).order_by(SeasonModel.id))).scalars().all()
            sea_ok = 0
            sea_bad = 0
            for sea in seasons:
                if await check_url_status(client, sea.poster_url):
                    sea_ok += 1
                else:
                    sea_bad += 1
                    print(f"  [VERIFY FAIL] Season {sea.id} (Series {sea.series_id} S{sea.season_number}): {sea.poster_url}")

    print("\n==========================================================")
    print(f"FINAL AUDIT SUMMARY:")
    print(f"  Movies : {m_ok}/{len(movies)} ({m_ok/len(movies)*100:.1f}%) working HTTP 200 posters (Broken: {m_bad})")
    print(f"  Series : {s_ok}/{len(series)} ({s_ok/len(series)*100:.1f}%) working HTTP 200 posters (Broken: {s_bad})")
    print(f"  Seasons: {sea_ok}/{len(seasons)} ({sea_ok/len(seasons)*100:.1f}%) working HTTP 200 posters (Broken: {sea_bad})")
    print("==========================================================")

if __name__ == "__main__":
    asyncio.run(main())
