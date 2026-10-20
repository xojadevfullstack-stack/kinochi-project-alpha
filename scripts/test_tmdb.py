import asyncio
import os
import sys

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from app.infrastructure.external.tmdb_client import TMDbClient
from app.core.config import settings

async def main():
    print(f"TMDB_API_KEY present: {bool(settings.TMDB_API_KEY)}")
    client = TMDbClient()
    print("Testing search for 'Interstellar'...")
    res = await client.search("Interstellar", content_type="movie")
    if res:
        print(f"Success! Found {len(res)} results. First: {res[0]['title']} -> {res[0]['poster_url']}")
    else:
        print("Failed to find results.")

    print("\nTesting details for tmdb_id=157336 (Interstellar)...")
    details = await client.get_details(157336, kind="movie")
    if details:
        print(f"Success! Details poster: {details.get('poster_url')}")
    else:
        print("Failed to get details.")

if __name__ == "__main__":
    asyncio.run(main())
