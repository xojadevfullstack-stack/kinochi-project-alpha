import asyncio
import os
import sys
import re
import httpx
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))

from app.core.config import settings

TMDB_API_KEY = settings.TMDB_API_KEY.strip()
HEADERS = {
    "Authorization": f"Bearer {TMDB_API_KEY}",
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0"
}

from scripts.migrate_all_movies_individual_topics import ALL_MOVIES

async def main():
    async with httpx.AsyncClient(headers=HEADERS, timeout=8.0) as client:
        real_map = {}
        for m in ALL_MOVIES:
            tid = m.get("tmdb_id")
            if not tid:
                continue
            
            poster = None
            for lang in ["ru-RU", "en-US"]:
                try:
                    r = await client.get(f"https://api.themoviedb.org/3/movie/{tid}", params={"language": lang})
                    if r.status_code == 200:
                        pp = r.json().get("poster_path")
                        if pp:
                            poster = f"https://image.tmdb.org/t/p/w500{pp}"
                            break
                except Exception:
                    pass

            if poster:
                real_map[tid] = poster

        # Patch file
        file_path = "scripts/migrate_all_movies_individual_topics.py"
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        count = 0
        for tid, url in real_map.items():
            pattern = rf'("tmdb_id":\s*{tid},\s*"poster_url":\s*")[^"]+(")'
            new_content, n = re.subn(pattern, rf'\g<1>{url}\g<2>', content)
            if n > 0:
                content = new_content
                count += n

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"Patched {count} posters in {file_path}")

if __name__ == "__main__":
    asyncio.run(main())
