import asyncio
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from telethon import TelegramClient
from telethon.sessions import StringSession

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    channels = [-1003941035700, -1003926001543]
    keywords = ["2-qism", "2-bolim", "2-bo'lim", "2-bo`lim", "2-qism", "part 2", "part 1", "2-bolak", "2-bo'lak", "1-bolak", "1-bo'lak"]

    for ch_id in channels:
        print(f"\n================ SCANNING CHANNEL: {ch_id} ================")
        found = []
        async for msg in client.iter_messages(ch_id, limit=3500):
            # Check text or filename
            text = (msg.message or "").lower()
            fname = ""
            if msg.file and msg.file.name:
                fname = msg.file.name.lower()
            
            combined = text + " " + fname
            for kw in ["2-qism", "2-bo'lim", "2-bolim", "part 2", "2-bolak", "2-bo'lak", "part2", "2-chi qism"]:
                if kw in combined:
                    # Filter out TV series episodes (e.g. S01E02 or similar)
                    # We are looking for MOVIES that are split into 2 parts
                    first_line = (msg.message or fname or "unknown").strip().split('\n')[0]
                    sz = (msg.file.size / (1024*1024)) if (msg.file and msg.file.size) else 0
                    found.append((msg.id, first_line[:90], sz))
                    break
        print(f"Found {len(found)} candidate messages:")
        for fid, ftxt, fsz in found:
            print(f"  [Msg {fid}] ({fsz:.1f} MB) {ftxt}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
