import asyncio
from app.infrastructure.db.session import engine
from sqlalchemy import text

async def check_pages():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, title, slug, is_active FROM pages"))
        rows = result.fetchall()
        for row in rows:
            print(dict(row._mapping))

if __name__ == "__main__":
    asyncio.run(check_pages())
