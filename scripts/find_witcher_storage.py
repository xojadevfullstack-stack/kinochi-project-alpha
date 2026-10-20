import asyncio
import os
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TARGET_STORAGE = -1003762157591

async def find_witcher():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    print("Searching for the 1748.7 MB / 1:03:46 video in TARGET_STORAGE...")
    # Search by text "Qit'adagi ov" or "Witcher" or "Jodugar"
    async for msg in client.iter_messages(TARGET_STORAGE, search="Qit'adagi ov", limit=10):
        print(f"Found by text 'Qit'adagi ov': ID={msg.id}")
        if msg.video or msg.document:
            media = msg.video or msg.document
            print(f"  size: {round(media.size/(1024*1024), 1)}MB, text: {msg.message[:80]}")

    async for msg in client.iter_messages(TARGET_STORAGE, search="Jodugar", limit=10):
        print(f"Found by text 'Jodugar': ID={msg.id}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(find_witcher())
