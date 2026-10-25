import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def test_codes():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    bot = 'UzmovieTV_Bot'
    codes = ["6125", "6134", "6150", "6165", "441"]

    for code in codes:
        print(f"\n--- Sending code '{code}' to @{bot} ---")
        sent = await client.send_message(bot, code)
        await asyncio.sleep(4.0)
        async for m in client.iter_messages(bot, limit=5):
            if m.id > sent.id:
                has_file = bool(m.file)
                f_name = m.file.name if m.file else None
                f_size = round(m.file.size / 1024 / 1024, 1) if m.file else 0
                txt = (m.text or "[No text]").replace("\n", " ")[:120]
                print(f"Msg {m.id} | Has file: {has_file} ({f_name}, {f_size} MB) | Text: {txt}")
                if m.buttons:
                    print("  Buttons:")
                    for row in m.buttons:
                        print("   ", [b.text for b in row])

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_codes())
