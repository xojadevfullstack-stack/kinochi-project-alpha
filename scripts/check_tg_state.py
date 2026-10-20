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

    supergroup_id = -1003847632555
    storage_id = -1003762157591

    print("Checking Supergroup topics...")
    from telethon.tl.functions.messages import GetForumTopicsRequest
    msgs = await client.get_messages(supergroup_id, ids=[4, 5, 12, 13, 45, 46])
    for m in msgs:
        if m:
            media_type = type(m.media).__name__ if m.media else "None"
            text_p = (m.message or "")[:60].replace("\n", " ").encode("ascii", "replace").decode("ascii")
            print(f"Msg {m.id}: reply_to={m.reply_to}, media={media_type}, text='{text_p}'")
        else:
            print("None")

    print("\nChecking Storage Channel latest messages...")
    st_msgs = await client.get_messages(storage_id, limit=10)
    for m in reversed(st_msgs):
        media_type = type(m.media).__name__ if m.media else "None"
        text_preview = (m.message or "")[:40].replace("\n", " ").encode("ascii", "replace").decode("ascii")
        print(f"   Storage Msg {m.id}: media={media_type}, text='{text_preview}'")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
