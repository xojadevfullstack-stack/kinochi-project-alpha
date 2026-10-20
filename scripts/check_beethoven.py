import os
import sys
import asyncio
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))

from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text

async def main():
    async with async_session_factory() as session:
        r = await session.execute(text("SELECT id, title, tmdb_id, poster_url FROM movies WHERE title ILIKE '%betxoven%' ORDER BY id"))
        rows = r.fetchall()
        print(f"Found {len(rows)} Beethoven movies:")
        for row in rows:
            print(f"  {row[0]} | {row[1]} | tmdb: {row[2]} | {row[3]}")

if __name__ == "__main__":
    asyncio.run(main())
