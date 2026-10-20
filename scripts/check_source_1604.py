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

async def check():
    client = TelegramClient(StringSession(os.getenv("TELEGRAM_STRING_SESSION")), int(os.getenv("TELEGRAM_API_ID")), os.getenv("TELEGRAM_API_HASH"))
    await client.connect()

    for ch in [-1003926001543, -1003941035700]:
        try:
            m = await client.get_messages(ch, ids=1604)
            if m:
                print(f"Channel {ch} Msg 1604:")
                print(f"  size: {getattr(m.file, 'size', None)}")
                print(f"  duration: {getattr(m.file, 'duration', None)}")
                print(f"  name: {getattr(m.file, 'name', None)}")
                print(f"  text: {(m.message or '')[:100]}")
            else:
                print(f"Channel {ch} Msg 1604: NOT FOUND")
        except Exception as e:
            print(f"Channel {ch} error: {e}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check())
