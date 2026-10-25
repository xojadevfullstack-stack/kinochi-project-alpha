import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def check_bots():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    for bot in ['asilmediabot', 'UzmovieTV_Bot']:
        print(f"=== Testing @{bot} ===")
        try:
            sent = await client.send_message(bot, "qashqirlar makoni")
            await asyncio.sleep(4)
            async for m in client.iter_messages(bot, limit=5):
                if m.id > sent.id:
                    txt = m.text[:120] if m.text else "[No text]"
                    print(f"Msg {m.id}: {txt}")
                    if m.buttons:
                        print("Buttons:")
                        for row in m.buttons:
                            print("  ", [b.text for b in row])
        except Exception as e:
            print(f"Error testing @{bot}: {e}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check_bots())
