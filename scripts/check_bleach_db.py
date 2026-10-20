import asyncio
import sys
import os
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

async def main():
    async with async_session_factory() as session:
        s_res = await session.execute(text("SELECT id, title, created_at, status, publish_status FROM series WHERE title ILIKE '%bleach%' OR title ILIKE '%blich%'"))
        s_rows = s_res.fetchall()
        print(f"Total Bleach series rows: {len(s_rows)}")
        for sr in s_rows:
            print(f"  Series ID={sr[0]} Title='{sr[1]}' Status={sr[3]} Pub={sr[4]}")

        query = text("""
            SELECT s.id as series_id, s.title, sn.id as season_id, sn.season_number, ep.id as ep_id, ep.episode_number, ep.display_code, ep.code, tr.storage_channel_message_id, ep.source_message_id, tr.telegram_file_id
            FROM series s
            JOIN seasons sn ON sn.series_id = s.id
            JOIN episodes ep ON ep.season_id = sn.id
            LEFT JOIN episode_translations tr ON tr.episode_id = ep.id
            WHERE s.title ILIKE '%blich%' OR s.title ILIKE '%bleach%'
            ORDER BY sn.season_number, ep.episode_number
        """)
        res = await session.execute(query)
        rows = res.fetchall()
        print(f"Total episodes for Bleach in DB: {len(rows)}")
        for r in rows:
            print(f"S{r[3]}E{r[5]} (ep_id={r[4]} code={r[7]} disp={r[6]}): storage_msg_id={r[8]} file_id={r[10]} source_msg_id={r[9]}")

if __name__ == "__main__":
    asyncio.run(main())
