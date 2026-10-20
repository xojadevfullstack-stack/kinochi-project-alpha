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

async def check():
    async with async_session_factory() as session:
        for disp in ['S1-CH1', 'S1-CH2', 'S2-CH1', 'S2-CH2']:
            res = await session.execute(text("""
                SELECT ep.id, ep.code, ep.display_code, s.title, sn.season_number, ep.episode_number, tr.storage_channel_message_id
                FROM episodes ep
                JOIN seasons sn ON sn.id = ep.season_id
                JOIN series s ON s.id = sn.series_id
                LEFT JOIN episode_translations tr ON tr.episode_id = ep.id
                WHERE upper(ep.display_code) = :disp
                ORDER BY ep.id
            """), {'disp': disp})
            rows = res.fetchall()
            print(f"=== {disp}: {len(rows)} matching episodes ===")
            for r in rows:
                print(f"  id={r[0]} code={r[1]} s_title='{r[3]}' S{r[4]}E{r[5]} st_id={r[6]}")

if __name__ == "__main__":
    asyncio.run(check())
