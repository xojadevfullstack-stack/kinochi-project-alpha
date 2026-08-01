import asyncio
import os
import sys
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv(os.path.abspath('backend/.env'))

async def main():
    engine = create_async_engine(os.getenv("DATABASE_URL"))
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT id, title, source_chat_id, source_topic_id FROM movies WHERE source_chat_id='-1003941035700';"))
        rows = result.fetchall()
        for r in rows:
            print("MOVIE:", r)
        
        result2 = await conn.execute(text("SELECT id, chat_id, topic_id FROM sources;"))
        rows2 = result2.fetchall()
        for r in rows2:
            print("SOURCE:", r)
            
if __name__ == "__main__":
    asyncio.run(main())
