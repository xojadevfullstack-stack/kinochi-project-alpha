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

async def check():
    client = TelegramClient(StringSession(os.getenv("TELEGRAM_STRING_SESSION")), int(os.getenv("TELEGRAM_API_ID")), os.getenv("TELEGRAM_API_HASH"))
    await client.connect()

    print("Checking TARGET_STORAGE range 1580..1640:")
    for mid in range(1580, 1635):
        try:
            m = await client.get_messages(TARGET_STORAGE, ids=mid)
            if m and (m.video or m.document):
                fname = getattr(m.file, 'name', '')
                dur = getattr(m.file, 'duration', 0)
                first_line = (m.message or '').split('\n')[0]
                print(f"  ST Msg {mid}: file='{fname}' dur={dur}s text='{first_line}'")
        except Exception as e:
            print(f"  ST Msg {mid} error: {e}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check())
