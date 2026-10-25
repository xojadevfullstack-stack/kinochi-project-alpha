import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def check_old_topics():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    old_chat = -1003941035700
    m33418 = await client.get_messages(old_chat, ids=33418)
    print("Topic 33418 root msg:", m33418.text[:200] if m33418 and m33418.text else "None")

    # Let's search for "qashqirlar" across root topic messages in old_chat
    print("\nLooking for other qashqirlar messages in old_chat:")
    async for m in client.iter_messages(old_chat, search="qashqirlar makoni", limit=50):
        if m.reply_to is None:
            print(f"Root Msg {m.id}: {m.text[:100] if m.text else 'None'}")
        elif m.id < 33450 and m.id > 33415:
            print(f"Near 33418 Msg {m.id}: {m.text[:100] if m.text else 'None'}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check_old_topics())
