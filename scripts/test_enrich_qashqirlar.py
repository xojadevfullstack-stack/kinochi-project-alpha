import sys, os
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath("."))
sys.path.insert(0, os.path.abspath("backend"))
from dotenv import load_dotenv
load_dotenv(".env.local")
load_dotenv("backend/.env")

import asyncio
from scraper.smart_enricher import enrich_movie_smart

async def test_enrich():
    items = [
        ("Kurtlar Vadisi: Irak", 2006, "movie"),
        ("Kurtlar Vadisi: Filistin", 2011, "movie"),
        ("Kurtlar Vadisi: Vatan", 2017, "movie"),
        ("Kurtlar Vadisi", 2003, "series"),
    ]

    for title, year, m_type in items:
        meta = await enrich_movie_smart(title, year=year, media_type=m_type)
        print(f"\n=== {title} ({m_type}) ===")
        print(f"Title: {meta.get('title')}")
        print(f"Orig: {meta.get('original_title')}")
        print(f"TMDb: {meta.get('tmdb_id')} | Year: {meta.get('release_year')} | IMDb: {meta.get('imdb_rating')}")
        print(f"Poster: {meta.get('poster_url')}")
        print(f"Genres: {meta.get('genres')}")
        print(f"Desc: {(meta.get('description') or '')[:100]}...")

if __name__ == "__main__":
    asyncio.run(test_enrich())
