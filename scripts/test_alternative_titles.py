import asyncio
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

BASE_DIR = r"c:\Users\Администратор\Desktop\kino bot project\kinochi project"
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

QUERIES = [
    # Prison Break
    "Qamoqdan qochish",
    "Qamoq",
    # Breaking Bad
    "Tubanlik sari",
    "Og'ir damlar",
    "Barcha yomonliklar",
    # Better Call Saul
    "Solga",
    "Saul",
    # BBC Sherlock
    "Sherlok Xolms",
    "Sherlok",
    # Squid Game
    "Kalmar",
    # All of us are dead
    "Biz barchamiz o'likmiz",
    "Biz olikmiz",
    "Zombi",
]

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    for ch_id in [-1003941035700, -1003926001543]:
        print(f"\n============================\nChannel {ch_id}:")
        for q in QUERIES:
            count = 0
            async for m in client.iter_messages(ch_id, search=q, limit=5):
                count += 1
                txt = (m.message or "")[:60].replace("\n", " ").encode("ascii", "replace").decode()
                print(f"  [{q}] Msg {m.id}: {txt}")
            if count == 0:
                pass

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
