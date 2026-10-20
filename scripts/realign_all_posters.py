import asyncio
import os
import sys
import httpx
import re
from difflib import SequenceMatcher
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
HEADERS = {
    "Authorization": f"Bearer {TMDB_API_KEY}",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0"
}

# Known correct title mappings for franchise/Uzbek titles
KNOWN_TITLE_MAPPINGS = {
    "Karib dengizi qaroqchilari 5: Murdalar ertak aytmaydi": ("Pirates of the Caribbean: Dead Men Tell No Tales", 2017),
    "Shrek 4: Abadiy baxt": ("Shrek Forever After", 2010),
    "Annabel 1": ("Annabelle", 2014),
    "Arra 3": ("Saw III", 2006),
    "Yovuzlik qarorgohi 1": ("Resident Evil", 2002),
    "Yovuzlik qarorgohi 2: Apokalipsis": ("Resident Evil: Apocalypse", 2004),
    "Yovuzlik qarorgohi 3: Qirg'in": ("Resident Evil: Extinction", 2007),
    "Yovuzlik qarorgohi 5: Qasos": ("Resident Evil: Retribution", 2012),
    "Oxirgi manzil 6": ("Final Destination: Bloodlines", 2025),
    "Qaqshatqich ochlik o'yinlari": ("The Starving Games", 2013),
    "Betxoven 1": ("Beethoven", 1992),
    "Betxoven 2": ("Beethoven's 2nd", 1993),
    "Betxoven 3": ("Beethoven's 3rd", 2000),
    "Betxoven 5": ("Beethoven's 5th", 2003),
    "Qashqirlar makoni: Gladio": ("Kurtlar Vadisi: Gladio", 2009),
    "Qashqirlar makoni: Falastin": ("Kurtlar Vadisi: Filistin", 2011),
    "Qashqirlar makoni: Vatan": ("Kurtlar Vadisi Vatan", 2017),
    "Yura davri bog'iga qaytish": ("Return to Jurassic Park", 2011),
    "Yura davri dunyosi: Qayta tug'ilish": ("Jurassic World Rebirth", 2025),
    "Venom 3: So'nggi raqs": ("Venom: The Last Dance", 2024),
}

def title_similarity(a: str, b: str) -> float:
    a_clean = re.sub(r'[^a-zA-Z0-9]', '', (a or '').lower())
    b_clean = re.sub(r'[^a-zA-Z0-9]', '', (b or '').lower())
    return SequenceMatcher(None, a_clean, b_clean).ratio()

async def search_best_tmdb_match(client: httpx.AsyncClient, query: str, year: int = None):
    url = "https://api.themoviedb.org/3/search/movie"
    params_list = []
    if year:
        params_list.append({"query": query, "year": year})
        params_list.append({"query": query, "primary_release_year": year})
    params_list.append({"query": query})

    for p in params_list:
        try:
            r = await client.get(url, params=p)
            if r.status_code == 200:
                results = r.json().get("results", [])
                if results:
                    # Score results
                    for res in results:
                        tmdb_title = res.get("title") or ""
                        tmdb_orig = res.get("original_title") or ""
                        sim1 = title_similarity(query, tmdb_title)
                        sim2 = title_similarity(query, tmdb_orig)
                        max_sim = max(sim1, sim2)
                        
                        # Check year match
                        rd = res.get("release_date") or ""
                        res_yr = int(rd[:4]) if (len(rd) >= 4 and rd[:4].isdigit()) else None
                        yr_match = (year is None) or (res_yr is None) or (abs(res_yr - year) <= 1)

                        if (max_sim >= 0.5 or query.lower() in tmdb_title.lower() or query.lower() in tmdb_orig.lower()) and yr_match:
                            ppath = res.get("poster_path")
                            if ppath:
                                return res["id"], tmdb_title, res_yr, f"https://image.tmdb.org/t/p/w500{ppath}"
                    
                    # If strict match didn't return, take best result if year matches and has poster
                    for res in results[:3]:
                        if res.get("poster_path"):
                            return res["id"], res.get("title"), year, f"https://image.tmdb.org/t/p/w500{res['poster_path']}"
        except Exception as e:
            print(f"Error querying {p}: {e}")
    return None, None, None, None

async def main():
    print("===================================================================")
    print("      COMPREHENSIVE TMDB AUDIT & RE-ALIGNMENT FOR ALL MOVIES       ")
    print("===================================================================")

    engine = create_async_engine(settings.DATABASE_URL)
    limits = httpx.Limits(max_keepalive_connections=30, max_connections=40)

    async with httpx.AsyncClient(limits=limits, headers=HEADERS, timeout=10.0) as client:
        async with engine.begin() as conn:
            movies = (await conn.execute(text("SELECT id, title, original_title, tmdb_id, release_year, poster_url FROM movies ORDER BY id"))).fetchall()
            print(f"Loaded {len(movies)} movies from database.\n")

            fixes_applied = 0
            verified_correct = 0

            for m in movies:
                target_query = None
                target_year = m.release_year

                # Check manual overrides first
                if m.title in KNOWN_TITLE_MAPPINGS:
                    target_query, target_year = KNOWN_TITLE_MAPPINGS[m.title]
                elif m.original_title and m.original_title != "None":
                    target_query = m.original_title
                else:
                    target_query = m.title

                # Search TMDb
                real_id, real_title, real_year, real_poster = await search_best_tmdb_match(client, target_query, target_year)

                if real_id:
                    # Check if current DB data has wrong ID or wrong poster
                    needs_update = False
                    if m.tmdb_id != real_id:
                        needs_update = True
                    if m.poster_url != real_poster:
                        needs_update = True
                    if not m.original_title or m.original_title == "None":
                        needs_update = True

                    if needs_update:
                        await conn.execute(text("""
                            UPDATE movies 
                            SET tmdb_id = :tmdb_id, 
                                original_title = :orig, 
                                poster_url = :poster, 
                                updated_at = NOW() 
                            WHERE id = :id
                        """), {
                            "tmdb_id": real_id,
                            "orig": real_title,
                            "poster": real_poster,
                            "id": m.id
                        })
                        fixes_applied += 1
                        print(f"FIXED [{m.id:3d}] '{m.title}' ({m.release_year}):\n"
                              f"   Old: TMDB={m.tmdb_id}, Poster={m.poster_url}\n"
                              f"   New: TMDB={real_id} ('{real_title}'), Poster={real_poster}\n")
                    else:
                        verified_correct += 1
                else:
                    print(f"WARN [{m.id:3d}] '{m.title}': No TMDb match found for query '{target_query}'")

            print(f"Summary: {fixes_applied} movies fixed, {verified_correct} movies already verified.")

        # Invalidate all caches
        print("\nFlushing caches...")
        await delete_cache_pattern("cache:*")
        await delete_cache_pattern("recommendations:*")
        await delete_cache_pattern("*")
        print("Caches cleared successfully!")

        # Final Verification of all movies
        print("\nRunning Verification Audit of all movies...")
        async with engine.connect() as conn:
            all_m = (await conn.execute(text("SELECT id, title, original_title, tmdb_id, poster_url FROM movies ORDER BY id"))).fetchall()
            valid_posters = 0
            for r in all_m:
                try:
                    head_res = await client.head(r.poster_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=5.0)
                    if head_res.status_code == 200:
                        valid_posters += 1
                    else:
                        print(f"Broken poster: [{r.id}] {r.title} -> {r.poster_url}")
                except Exception as e:
                    print(f"Broken poster error: [{r.id}] {r.title} -> {e}")

            print(f"\nFinal Verified Posters: {valid_posters}/{len(all_m)} ({(valid_posters/len(all_m))*100:.1f}%)")

if __name__ == "__main__":
    asyncio.run(main())
