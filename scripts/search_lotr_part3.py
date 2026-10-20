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
    await client.get_dialogs()

    for ch in [-1003926001543, -1003941035700]:
        print(f"=== Channel {ch} ===")
        for q in ["Uzuklar", "Hukmdori", "Qirolning"]:
            async for m in client.iter_messages(ch, search=q, limit=20):
                txt = (m.message or "").replace("\n", " ")[:70]
                fname = m.file.name if m.file else "None"
                print(f"[{ch}] Msg {m.id}: file='{fname}' | txt='{txt}'")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
