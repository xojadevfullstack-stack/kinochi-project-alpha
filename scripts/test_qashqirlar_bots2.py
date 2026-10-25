import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def test_more_queries():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    bot = 'asilmediabot'
    queries = ["Muro", "Gladio", "Pistirma", "Kurtlar vadisi"]

    for q in queries:
        print(f"\n=== Query: '{q}' to @{bot} ===")
        sent = await client.send_message(bot, q)
        await asyncio.sleep(3.5)
        async for m in client.iter_messages(bot, limit=4):
            if m.id > sent.id:
                txt = (m.text or "[No text]").replace("\n", " ")[:100]
                print(f"Msg {m.id}: {txt}")
                if m.buttons:
                    print("Buttons:")
                    for row in m.buttons:
                        print("  ", [b.text for b in row])

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_more_queries())
