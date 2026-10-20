import asyncio
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv(".env.local")
load_dotenv("backend/.env")
load_dotenv(".env")

from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text

async def main():
    async with async_session_factory() as session:
        movies_cnt = (await session.execute(text("SELECT count(*) FROM movies"))).scalar()
        series_cnt = (await session.execute(text("SELECT count(*) FROM series"))).scalar()
        episodes_cnt = (await session.execute(text("SELECT count(*) FROM episodes"))).scalar()
        translations_cnt = (await session.execute(text("SELECT count(*) FROM movie_translations"))).scalar()
        page_movies = (await session.execute(text("SELECT count(*) FROM page_movie"))).scalar()
        page_series = (await session.execute(text("SELECT count(*) FROM page_series"))).scalar()

        print("=== DATABASE AUDIT SUMMARY ===")
        print(f"Total Movies: {movies_cnt}")
        print(f"Total Movie Translations: {translations_cnt}")
        print(f"Total Series: {series_cnt}")
        print(f"Total Episodes: {episodes_cnt}")
        print(f"Page-Movie Links: {page_movies}")
        print(f"Page-Series Links: {page_series}")

        # Check split movies in DB
        res = await session.execute(text("""
            SELECT id, title, source_topic_id, code 
            FROM movies 
            WHERE title ILIKE '%titanik%' 
               OR title ILIKE '%interstellar%' 
               OR title ILIKE '%uzuklar hukmdori%'
            ORDER BY id ASC
        """))
        print("\n=== SPLIT MOVIES AUDIT ===")
        for row in res.fetchall():
            print(f"ID {row[0]}: {row[1]} | Topic: {row[2]} | Code: {row[3]}")

if __name__ == "__main__":
    asyncio.run(main())
