import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import settings

async def check():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema='public';"))
        tables = [r[0] for r in res.fetchall()]
        print("Tables:", tables)

        if "movies" in tables:
            res = await conn.execute(text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name='movies';"))
            print("Movies columns:", res.fetchall())
        
asyncio.run(check())
