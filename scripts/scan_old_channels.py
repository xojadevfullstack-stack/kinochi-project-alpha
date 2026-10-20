import asyncio
import os
import sys
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

BASE_DIR = r"c:\Users\Администратор\Desktop\kino bot project\kinochi project"
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    for ch_id in [-1003941035700, -1003926001543]:
        ent = await client.get_entity(ch_id)
        title = getattr(ent, 'title', str(ent)).encode('ascii', 'replace').decode()
        print(f"\n============================\nChannel {ch_id} ({title}):")
        msgs = await client.get_messages(ch_id, limit=15)
        for m in reversed(msgs):
            media_type = type(m.media).__name__ if m.media else "None"
            text_p = (m.message or "")[:60].replace("\n", " ").encode("ascii", "replace").decode()
            print(f"   Msg {m.id}: media={media_type}, text='{text_p}'")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
