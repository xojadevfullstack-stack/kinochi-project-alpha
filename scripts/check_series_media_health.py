import asyncio
import os
import sys
from sqlalchemy import text
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.infrastructure.db.session import async_session_factory

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def check_all():
    async with async_session_factory() as session:
        res = await session.execute(text("""
            SELECT s.id, s.title, COUNT(ep.id) as ep_count, 
                   COUNT(CASE WHEN tr.storage_channel_message_id IS NULL AND tr.telegram_file_id IS NULL THEN 1 END) as missing_media
            FROM series s
            JOIN seasons sn ON sn.series_id = s.id
            JOIN episodes ep ON ep.season_id = sn.id
            LEFT JOIN episode_translations tr ON tr.episode_id = ep.id
            GROUP BY s.id, s.title
            HAVING COUNT(CASE WHEN tr.storage_channel_message_id IS NULL AND tr.telegram_file_id IS NULL THEN 1 END) > 0
        """))
        rows = res.fetchall()
        print("Series with missing media:", len(rows))
        for r in rows:
            print(f"  id={r[0]} title='{r[1]}' eps={r[2]} missing={r[3]}")

if __name__ == "__main__":
    asyncio.run(check_all())
