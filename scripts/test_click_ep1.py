import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def test_ep1():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    bot = 'asilmediabot'
    # Find message 292609 (or recent message with buttons)
    m = await client.get_messages(bot, ids=292609)
    if not m or not m.buttons:
        print("Message 292609 not found, searching recent...")
        async for msg in client.iter_messages(bot, limit=5):
            if msg.buttons and any(b.text == '1' for row in msg.buttons for b in row):
                m = msg
                break

    print(f"Card message {m.id} found. Clicking button '1' (row 0, col 0)...")
    await m.click(0, 0)
    await asyncio.sleep(4.0)

    async for reply in client.iter_messages(bot, limit=3):
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
    asyncio.run(test_ep1())
