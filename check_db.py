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
        result = await conn.execute(text("SELECT id, movie_id, language, telegram_file_id, storage_channel_message_id FROM movie_translations WHERE telegram_file_id='mock_file_id_123';"))
        rows = result.fetchall()
        for r in rows:
            print("DB ROW:", r)
            
if __name__ == "__main__":
    asyncio.run(main())
