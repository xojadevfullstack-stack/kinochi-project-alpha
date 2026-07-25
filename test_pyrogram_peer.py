import asyncio
import os
from pyrogram import Client

BOT_TOKEN = os.environ.get("BOT_TOKEN")
API_ID = int(os.environ.get("TELEGRAM_API_ID", "0"))
API_HASH = os.environ.get("TELEGRAM_API_HASH", "")
CHAT_ID = int(os.environ.get("STORAGE_CHANNEL_ID", "0"))

async def test():
    print(f"Testing Pyrogram get_chat with Bot Token: {BOT_TOKEN[:10]}... API_ID: {API_ID}")
    app = Client("test_session", bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH, in_memory=True)
    async with app:
        try:
            chat = await app.get_chat(CHAT_ID)
            print("SUCCESS! Chat title:", chat.title)
        except Exception as e:
            print("FAILED get_chat:", repr(e))
            
            # Alternative trick: Can we send to username?
            pass

if __name__ == "__main__":
    asyncio.run(test())
