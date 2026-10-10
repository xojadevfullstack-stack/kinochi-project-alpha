import asyncio
import sys
import os
from dotenv import load_dotenv

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.category import CategoryModel
from sqlalchemy import select

async def main():
    async with async_session_factory() as session:
        res = await session.execute(select(CategoryModel).order_by(CategoryModel.id))
        for c in res.scalars().all():
            print(f"ID={c.id}, Name={c.name}, Slug={c.slug}")

if __name__ == "__main__":
    asyncio.run(main())
