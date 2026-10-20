import asyncio
import os
import sys
import httpx
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
from app.core.config import settings

TMDB_API_KEY = settings.TMDB_API_KEY.strip()
HEADERS = {
    "Authorization": f"Bearer {TMDB_API_KEY}",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0"
}

# Import BATCH2_MOVIES from script
from scripts.migrate_batch2_movies_individual_topics import BATCH2_MOVIES

async def main():
    async with httpx.AsyncClient(headers=HEADERS, timeout=10.0) as client:
        real_posters = {}
        for m in BATCH2_MOVIES:
            tid = m.get("tmdb_id")
            if not tid:
                continue
            
            poster = None
            for lang in ["ru-RU", "en-US"]:
                url = f"https://api.themoviedb.org/3/movie/{tid}"
                try:
                    r = await client.get(url, params={"language": lang})
                    if r.status_code == 200:
                        pp = r.json().get("poster_path")
                        if pp:
                            poster = f"https://image.tmdb.org/t/p/w500{pp}"
                            break
                except Exception as e:
                    pass
            
            if not poster:
                try:
                    url = f"https://api.themoviedb.org/3/movie/{tid}/images"
                    r = await client.get(url)
                    if r.status_code == 200:
                        posters = r.json().get("posters", [])
                        if posters:
                            poster = f"https://image.tmdb.org/t/p/w500{posters[0]['file_path']}"
                except Exception:
                    pass

            if poster:
                # verify with HEAD
                try:
                    h = await client.head(poster, headers={"User-Agent": "Mozilla/5.0"}, timeout=5.0)
                    if h.status_code == 200:
                        real_posters[tid] = poster
                        print(f"OK {tid} ({m['title']}) -> {poster}")
                    else:
                        print(f"HEAD FAIL {tid}: {h.status_code}")
                except Exception as e:
                    print(f"HEAD ERROR {tid}: {e}")
            else:
                print(f"NO POSTER {tid} ({m['title']})")

        with open("batch2_real_posters.json", "w", encoding="utf-8") as f:
            json.dump(real_posters, f, indent=2, ensure_ascii=False)
        print(f"\nSaved {len(real_posters)} real posters to batch2_real_posters.json")

if __name__ == "__main__":
    asyncio.run(main())
