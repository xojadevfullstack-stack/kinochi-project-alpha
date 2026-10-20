import asyncio
import os
import sys
import json

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from app.infrastructure.external.tmdb_client import TMDbClient

SERIES_IDS = {
    "Breaking Bad": 1396,
    "The Boys": 76479,
    "Sherlock": 19885,
    "The Continental": 114461,
    "All of Us Are Dead": 99966,
    "Dark": 70523,
    "The Witcher": 71912,
    "Vikings": 44217,
    "Prison Break": 2288,
    "Teen Wolf": 34524
}

async def main():
    client = TMDbClient()
    results = {}
    for name, tid in SERIES_IDS.items():
        det = await client.get_details(tid, kind="tv")
        if det:
            print(f"[{name}] (TMDB {tid}): poster={det.get('poster_url')}")
            results[name] = {
                "tmdb_id": tid,
                "poster_url": det.get("poster_url"),
                "vote_average": det.get("vote_average"),
                "overview": det.get("overview"),
                "name": det.get("name")
            }
        else:
            print(f"[{name}] FAILED to get details!")

    with open("scripts/real_series_metadata.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
