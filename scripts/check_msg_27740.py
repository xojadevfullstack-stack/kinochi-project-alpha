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

    source_1 = -1003926001543
    m = await client.get_messages(source_1, ids=27740)
    if m:
        print(f"Source 1 msg 27740: file={getattr(m.file, 'name', '')}, text:\n{m.message}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
