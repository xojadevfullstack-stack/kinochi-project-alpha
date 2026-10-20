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

    found = []
    for ch in [-1003941035700, -1003926001543]:
        for q in [".p1", ".p2", ".part1", ".part2", "p1.mp4", "p2.mp4", "1-bo'lak", "2-bo'lak"]:
            async for m in client.iter_messages(ch, search=q, limit=100):
                if m.file and m.file.size > 200 * 1024 * 1024:
                    fn = m.file.name or ""
                    txt = (m.message or "").replace("\n", " ")
                    if any(w in txt.lower() or w in fn.lower() for w in ["mavsum", "robot", "vampirlar", "original", "qirollik", "daredevil", "shtam"]):
                        continue
                    if not any(x[0] == ch and x[1] == m.id for x in found):
                        found.append((ch, m.id, fn, m.file.size / (1024*1024), txt[:70]))

    print(f"Total split movies found: {len(found)}")
    for ch, mid, fn, sz, txt in found:
        print(f"[{ch}] Msg {mid}: '{fn}' ({sz:.1f} MB) | txt: '{txt}'")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
