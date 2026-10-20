import asyncio
import sys
from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def check():
    async with async_session_factory() as session:
        res = await session.execute(text('SELECT id, title FROM series ORDER BY id'))
        for r in res.fetchall():
            print(f"Series ID={r[0]}: '{r[1]}'")

if __name__ == '__main__':
    asyncio.run(check())
