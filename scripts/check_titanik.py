import asyncio
import os
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

BASE_DIR = r"c:\Users\Администратор\Desktop\kino bot project\kinochi project"
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    storage_id = -1003762157591
    async for m in client.iter_messages(storage_id, search="Titanik", limit=10):
        print(f"Storage Msg {m.id}: {m.message[:80] if m.message else ''}")

    # Check movie 966 in DB
    from app.infrastructure.db.session import async_session_factory
    from sqlalchemy import text
    async with async_session_factory() as session:
        res = await session.execute(text("SELECT m.id, m.code, m.title, mt.storage_channel_message_id, mt.telegram_file_id FROM movies m LEFT JOIN movie_translations mt ON m.id = mt.movie_id WHERE m.id = 966"))
        print("Movie 966 in DB:", res.fetchall())

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
