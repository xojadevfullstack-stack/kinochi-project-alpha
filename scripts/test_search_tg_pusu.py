import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def search_telegram_pusu():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    # Search userbot dialogs/chats for pusu or pistirma
    print("Searching dialogs...")
    async for dialog in client.iter_dialogs():
        if any(w in dialog.name.lower() for w in ["qashqir", "pusu", "pistirma", "kurtlar"]):
            print(f"Dialog: {dialog.name} (ID: {dialog.id})")

    # Search global messages
    print("\nSearching global messages for 'qashqirlar makoni pistirma'...")
    try:
        from telethon.tl.functions.contacts import SearchRequest
        # or client.iter_messages with search
    except Exception:
        pass

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(search_telegram_pusu())
