import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def test_uzmovie_inline():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    bot = 'UzmovieTV_Bot'
    queries = [
        "qashqirlar makoni",
        "muro",
        "gladio",
        "pusu",
        "pistirma",
        "kurtlar vadisi",
        "qashqirlar makoni iroq",
        "qashqirlar makoni falastin",
        "qashqirlar makoni vatan"
    ]

    for q in queries:
        print(f"\n=== Inline query: '{q}' to @{bot} ===")
        try:
            results = await client.inline_query(bot, q)
            print(f"Results count: {len(results)}")
            for r in results[:5]:
                print(f"  Title: {getattr(r, 'title', None)} | Desc: {getattr(r, 'description', None)} | Type: {type(r).__name__}")
        except Exception as e:
            print(f"Error: {e}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_uzmovie_inline())
