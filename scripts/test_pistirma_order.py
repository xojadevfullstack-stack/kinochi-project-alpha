import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os, re
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def check_pistirma_order():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    old_chat = -1003941035700
    topic_id = 33418

    print("Checking first 25 messages in topic 33418 (chronological)...")
    msgs = []
    async for m in client.iter_messages(old_chat, reply_to=topic_id, reverse=True, limit=25):
        if m.file:
            txt = (m.text or "[No text]").replace("\n", " ")[:80]
            msgs.append((m.id, txt))

    for mid, txt in msgs:
        print(f"  Msg {mid} -> {txt}")

    # Check the last 15 messages (chronological)
    print("\nChecking last 15 messages in topic 33418 (chronological)...")
    last_msgs = []
    async for m in client.iter_messages(old_chat, reply_to=topic_id, limit=15):
        if m.file:
            txt = (m.text or "[No text]").replace("\n", " ")[:80]
            last_msgs.append((m.id, txt))

    for mid, txt in reversed(last_msgs):
        print(f"  Msg {mid} -> {txt}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check_pistirma_order())
