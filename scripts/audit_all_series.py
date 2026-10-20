import asyncio
import sys
import os

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text

async def audit():
    async with async_session_factory() as session:
        r = await session.execute(text("""
            SELECT s.id, s.title, ss.topic_id, count(DISTINCT sea.id) as seasons_count, count(ep.id) as eps_count
            FROM series s
            JOIN series_sources ss ON s.source_id = ss.id
            LEFT JOIN seasons sea ON s.id = sea.series_id
            LEFT JOIN episodes ep ON sea.id = ep.season_id
            GROUP BY s.id, s.title, ss.topic_id
            ORDER BY s.id ASC
        """))
        rows = r.fetchall()
        print("=== ALL SERIES IN DATABASE (NEW SUPERGROUP) ===")
        total_eps = 0
        for row in rows:
            print(f"Series ID {row[0]}: '{row[1]}' | Topic ID: {row[2]} | Seasons: {row[3]} | Episodes: {row[4]}")
            total_eps += row[4]
        print(f"Total Series: {len(rows)}")
        print(f"Total Episodes: {total_eps}")

if __name__ == "__main__":
    asyncio.run(audit())
