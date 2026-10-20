import asyncio
import os
import sys
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
from app.core.config import settings

HEADERS = {"Authorization": f"Bearer {settings.TMDB_API_KEY}", "Accept": "application/json"}

test_movies = [
    ("Kurtlar Vadisi: Gladio", 2009),
    ("Kurtlar Vadisi: Filistin", 2011),
    ("Kurtlar Vadisi Vatan", 2017),
    ("Beethoven", 1992),
    ("Beethoven's 2nd", 1993),
    ("Beethoven's 3rd", 2000),
    ("Beethoven's 5th", 2003),
    ("Resident Evil", 2002),
    ("Resident Evil: Apocalypse", 2004),
    ("Resident Evil: Extinction", 2007),
    ("Resident Evil: Retribution", 2012),
    ("Saw III", 2006),
    ("Shrek Forever After", 2010),
    ("Pirates of the Caribbean: Dead Men Tell No Tales", 2017),
    ("Annabelle", 2014),
    ("The Starving Games", 2013),
    ("Venom: The Last Dance", 2024),
    ("Jurassic World Rebirth", 2025),
    ("Return to Jurassic Park", 2011),
]

async def main():
    async with httpx.AsyncClient(headers=HEADERS) as client:
        for title, yr in test_movies:
            r = await client.get("https://api.themoviedb.org/3/search/movie", params={"query": title, "year": yr})
            results = r.json().get("results", [])
            if not results:
                r = await client.get("https://api.themoviedb.org/3/search/movie", params={"query": title})
                results = r.json().get("results", [])
            if results:
                best = results[0]
                print(f"{title:45s} ({yr}) -> TMDb ID: {best['id']:7d} | Title: '{best['title']}' ({best.get('release_date', '')[:4]}) | Poster: https://image.tmdb.org/t/p/w500{best.get('poster_path')}")
            else:
                print(f"{title} -> NOT FOUND")

if __name__ == "__main__":
    asyncio.run(main())
