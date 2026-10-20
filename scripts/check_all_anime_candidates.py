import asyncio
import os
import sys
from dotenv import load_dotenv
from sqlalchemy import text

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))

from app.infrastructure.db.session import async_session_factory

async def check():
    async with async_session_factory() as session:
        # Tables
        t_res = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name"))
        print("=== TABLES ===")
        for r in t_res.fetchall():
            print(r[0])

        # Movies count
        m_cnt = await session.execute(text("SELECT publish_status, count(id) FROM movies GROUP BY publish_status"))
        print("\n=== MOVIES BY STATUS ===")
        for r in m_cnt.fetchall():
            print(r)

        # Series count
        s_cnt = await session.execute(text("SELECT publish_status, count(id) FROM series GROUP BY publish_status"))
        print("\n=== SERIES BY STATUS ===")
        for r in s_cnt.fetchall():
            print(r)

        # Seed candidates
        try:
            sc = await session.execute(text("SELECT count(id), media_type FROM seed_candidates GROUP BY media_type"))
            print("\n=== SEED CANDIDATES ===")
            for r in sc.fetchall():
                print(r)
        except Exception as e:
            print("seed_candidates query failed:", e)

        # Check any table with anime
        print("\n=== SEARCHING ANY TITLE WITH ANIME ACROSS TABLES ===")
        for tbl in ['movies', 'series', 'seed_candidates', 'collections']:
            try:
                res = await session.execute(text(f"SELECT id, title FROM {tbl} WHERE title ILIKE '%anime%' OR title ILIKE '%naruto%' OR title ILIKE '%iblis%' OR title ILIKE '%titan%' OR title ILIKE '%slayer%' OR title ILIKE '%hunter%' OR title ILIKE '%tabiat%' OR title ILIKE '%dunyo%' LIMIT 20"))
                rows = res.fetchall()
                if rows:
                    print(f"Found in {tbl}:", rows)
            except Exception as e:
                pass

if __name__ == "__main__":
    asyncio.run(check())
