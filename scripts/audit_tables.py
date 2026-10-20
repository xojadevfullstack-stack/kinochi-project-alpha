import asyncio
import os
import sys

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"))
        tables = [r[0] for r in res.fetchall()]
        print("TABLES:")
        for t in tables:
            try:
                cnt = (await conn.execute(text(f'SELECT count(*) FROM "{t}"'))).scalar()
                print(f"  {t}: {cnt}")
            except Exception as e:
                print(f"  {t}: err {e}")

        # Check collections columns
        res = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='collections'"))
        cols = [r[0] for r in res.fetchall()]
        print("\nCOLLECTIONS COLUMNS:", cols)

if __name__ == "__main__":
    asyncio.run(main())
