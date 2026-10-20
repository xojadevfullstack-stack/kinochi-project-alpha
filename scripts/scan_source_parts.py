import asyncio
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv(".env.local")
load_dotenv("backend/.env")
load_dotenv(".env")

from telethon import TelegramClient
from telethon.sessions import StringSession

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    for channel_id in [-1003941035700, -1003926001543]:
        print(f"\nScanning range 1 to 2000 in channel {channel_id}")
        for start in range(1, 2000, 100):
            ids = list(range(start, start + 100))
            try:
                msgs = await client.get_messages(channel_id, ids=ids)
            except Exception as e:
                print(f"Error fetching range {start}..{start+100}: {e}")
                continue

            for m in msgs:
                if not m:
                    continue
                # We care about video/document media
                if not m.file:
                    continue
                sz_mb = m.file.size / (1024 * 1024)
                if sz_mb < 300: # movies or movie parts are typically > 300MB
                    continue

                text = (m.message or "").lower()
                fname = (m.file.name or "").lower()
                combined = text + " " + fname

                # check keywords
                targets = ["qism", "bo'lim", "bolim", "bo`lim", "bo'lak", "bolak", "part"]
                if any(k in combined for k in targets):
                    first_line = (m.message or fname).strip().split("\n")[0]
                    print(f"Msg {m.id} ({sz_mb:.1f} MB): {first_line} | file: {fname}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
