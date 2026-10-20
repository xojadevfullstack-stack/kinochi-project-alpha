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

    storage_id = -1003762157591
    source_1 = -1003926001543

    # Fetch msg 27517 from source_1
    m = await client.get_messages(source_1, ids=27517)
    if not m:
        print("Error: Msg 27517 not found")
        return

    print("Found source msg 27517. Sending to storage channel...")
    caption = (
        "🎬 Odisseya (2026)\n"
        "🔢 Kodi: 8P6XNL\n"
        "🇺🇿 Tili: O'zbekcha\n"
        "⭐ IMDb: 8.0/10\n"
        "🎭 Janr: Sarguzasht, Jangari, Fantastika"
    )
    sent_msg = await client.send_file(storage_id, m.media, caption=caption)
    print(f"Successfully uploaded to storage! Storage message ID: {sent_msg.id}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
