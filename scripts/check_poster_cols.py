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
        res = await conn.execute(text(
            "SELECT table_name, column_name FROM information_schema.columns "
            "WHERE column_name LIKE '%poster%' OR column_name LIKE '%image%' "
            "ORDER BY table_name"
        ))
        for r in res.fetchall():
            print(f"{r[0]}.{r[1]}")

if __name__ == "__main__":
    asyncio.run(main())
