import asyncio
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('.env')

async def main():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    
    old_chat = -1003941035700
    print(f"Scanning topics in old chat {old_chat}...")

    topics = []
    async for m in client.iter_messages(old_chat, limit=5000):
        if getattr(m, 'action', None) and type(m.action).__name__ == 'MessageActionTopicCreate':
            topics.append({
                "id": m.id,
                "title": m.action.title,
                "date": str(m.date)
            })

    print(f"Total topics found in old chat: {len(topics)}")
    for t in sorted(topics, key=lambda x: x["id"]):
        print(f"Topic {t['id']}: {t['title']}")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
