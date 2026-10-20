import asyncio
import os
import sys
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.types import PeerChannel

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

async def search_channels():
    client = TelegramClient(
        StringSession(os.getenv("TELEGRAM_STRING_SESSION")),
        int(os.getenv("TELEGRAM_API_ID")),
        os.getenv("TELEGRAM_API_HASH")
    )
    await client.connect()

    # Get dialogs to populate cache
    print("Fetching dialogs...")
    async for dialog in client.iter_dialogs():
        pass

    channels = [
        (-1003762157591, "Storage -1003762157591"),
        (-1003926001543, "Source 1 -1003926001543"),
        (-1003941035700, "Source 2 -1003941035700"),
        (-1003847632555, "Topic Chat -1003847632555")
    ]

    for chat_id, name in channels:
        print(f"\n--- Searching in {name} ---")
        try:
            entity = await client.get_entity(chat_id)
            async for m in client.iter_messages(entity, search="Odisseya", limit=20):
                print(f"  ID {m.id}: date={m.date} text={(m.message or '')[:80]} file={getattr(m.file, 'name', '')}")
            async for m in client.iter_messages(entity, search="Odyssey", limit=20):
                print(f"  ID {m.id}: date={m.date} text={(m.message or '')[:80]} file={getattr(m.file, 'name', '')}")
            async for m in client.iter_messages(entity, search="Odisey", limit=20):
                print(f"  ID {m.id}: date={m.date} text={(m.message or '')[:80]} file={getattr(m.file, 'name', '')}")
        except Exception as e:
            print(f"  Error searching {name}: {e}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(search_channels())
