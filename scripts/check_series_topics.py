import asyncio
import os
import sys
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text

async def main():
    async with async_session_factory() as session:
        sql = "SELECT id, title, source_id, source_type FROM series WHERE id >= 998"
        res = await session.execute(text(sql))
        print("=== SERIES TOPICS (NEW) ===")
        for r in res.fetchall():
            print(f"Series ID {r[0]}: {r[1]} -> source_id (topic): {r[2]}, type: {r[3]}")

if __name__ == "__main__":
    asyncio.run(main())
