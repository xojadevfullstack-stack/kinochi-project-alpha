import asyncio
import sys
from sqlalchemy import text
from app.infrastructure.db.session import async_session_factory

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def main():
    async with async_session_factory() as session:
        res = await session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name"))
        rows = [r[0] for r in res.fetchall()]
        print("Public Tables:", rows)

asyncio.run(main())
