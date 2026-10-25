import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def test_next_ep():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    bot = 'asilmediabot'
    m = await client.get_messages(bot, ids=292619)
    print(f"Clicking 'Keyingi qism' on Msg {m.id}...")
    await m.click(0, 0)
    await asyncio.sleep(4.0)

    async for reply in client.iter_messages(bot, limit=2):
        if reply.id > m.id:
            txt = (reply.text or "[No text]").replace("\n", " ")[:120]
            f_info = f"{reply.file.name} ({round(reply.file.size/1024/1024, 1)} MB)" if reply.file else "No file"
            print(f"Reply Msg {reply.id} | File: {f_info} | Text: {txt}")
            if reply.buttons:
                print("  Buttons:")
                for r in reply.buttons:
                    print("   ", [b.text for b in r])

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_next_ep())
