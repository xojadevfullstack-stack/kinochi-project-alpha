import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def inspect_old_pistirma():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    old_chat = -1003941035700
    topic_id = 33418

    print("Checking topic 33418 in old chat...")
    messages = []
    async for m in client.iter_messages(old_chat, reply_to=topic_id, limit=30):
        if m.file:
            txt = (m.text or "[No text]").replace("\n", " ")[:80]
            f_size = round(m.file.size / 1024 / 1024, 1)
            messages.append((m.id, m.file.name, f_size, txt))

    print(f"Sample of {len(messages)} messages:")
    for mid, fname, fsize, txt in messages[:15]:
        print(f"  Msg {mid} | File: {fname} ({fsize} MB) | Text: {txt}")

    # Count total messages in topic
    total = 0
    async for m in client.iter_messages(old_chat, reply_to=topic_id):
        if m.file:
            total += 1
    print(f"\nTotal video files in topic 33418: {total}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(inspect_old_pistirma())
