import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def test_asil_ids():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    bot = 'asilmediabot'
    items = [
        ("Iroq (2006)", "12090"),
        ("Falastin (2011)", "12403"),
        ("Vatan (2017)", "14932"),
        ("Series (2003)", "11153")
    ]

    for label, code in items:
        print(f"\n=== Testing {label} with '/start {code}' ===")
        sent = await client.send_message(bot, f"/start {code}")
        await asyncio.sleep(3.0)
        async for m in client.iter_messages(bot, limit=4):
            if m.id > sent.id:
                txt = (m.text or "[No text]").replace("\n", " ")[:120]
                print(f"Msg {m.id} | Has file: {bool(m.file)} | Text: {txt}")
                if m.buttons:
                    print("  Buttons:")
                    for r in m.buttons:
                        print("   ", [b.text for b in r])

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_asil_ids())
