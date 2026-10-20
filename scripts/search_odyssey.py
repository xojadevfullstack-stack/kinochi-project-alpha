import asyncio
import os
import sys
from sqlalchemy import text
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.infrastructure.db.session import async_session_factory

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def check():
    async with async_session_factory() as session:
        # Search movies
        res = await session.execute(text("""
            SELECT id, title, original_title, release_year, code, tmdb_id, poster_url 
            FROM movies 
            WHERE title ILIKE '%odisseya%' OR title ILIKE '%odiseyya%' OR title ILIKE '%odyssey%' 
               OR original_title ILIKE '%odyssey%' OR title ILIKE '%interstellar%'
               OR title ILIKE '%kosmik%' OR title ILIKE '%yulduzlararo%'
            ORDER BY id
        """))
        rows = res.fetchall()
        print(f"Found {len(rows)} movies:")
        for r in rows:
            print(f"  Movie ID={r[0]} Title='{r[1]}' Orig='{r[2]}' Year={r[3]} Code={r[4]} Poster={r[6]}")

        # Search series too just in case
        # Check translations for movie 808, 1008, 1009
        res_tr = await session.execute(text("SELECT movie_id, language, storage_channel_message_id, telegram_file_id FROM movie_translations WHERE movie_id IN (808, 1008, 1009)"))
        print("\nMovie translations:")
        for tr in res_tr.fetchall():
            print(f"  Movie {tr[0]}: st_id={tr[2]} file_id={tr[3]}")

    from telethon import TelegramClient
    from telethon.sessions import StringSession
    client = TelegramClient(StringSession(os.getenv("TELEGRAM_STRING_SESSION")), int(os.getenv("TELEGRAM_API_ID")), os.getenv("TELEGRAM_API_HASH"))
    await client.connect()

    print("\nSource channel -1003941035700 messages 922, 924:")
    for mid in [922, 924]:
        m = await client.get_messages(-1003941035700, ids=mid)
        if m:
            print(f"  Msg {mid}: name='{getattr(m.file, 'name', '')}' dur={getattr(m.file, 'duration', 0)}s text='{(m.message or '')[:100]}'")

    print("\nStorage channel -1003762157591 messages 1633..1645:")
    for mid in range(1633, 1646):
        m = await client.get_messages(-1003762157591, ids=mid)
        if m:
            print(f"  Msg {mid}: name='{getattr(m.file, 'name', '')}' dur={getattr(m.file, 'duration', 0)}s text='{(m.message or '')[:60]}'")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check())
