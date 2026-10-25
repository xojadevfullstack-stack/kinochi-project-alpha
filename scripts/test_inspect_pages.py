import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def inspect_pages():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    bot = 'asilmediabot'
    m = await client.get_messages(bot, ids=292609)
    print(f"Initial card {m.id} buttons:")
    for row in m.buttons:
        print("  ", [b.text for b in row])

    # Let's find the '▶️' button and click it to go to page 2, 3, 4, 5
    for page in range(2, 6):
        # find the next button in m.buttons
        next_btn = None
        for r_idx, row in enumerate(m.buttons):
            for c_idx, b in enumerate(row):
                if '▶️' in b.text or '➡️' in b.text:
                    next_btn = (r_idx, c_idx)
                    break
            if next_btn:
                break

        if not next_btn:
            print("No next button found!")
            break

        print(f"\nClicking next button for page {page} at {next_btn}...")
        await m.click(next_btn[0], next_btn[1])
        await asyncio.sleep(2.0)
        m = await client.get_messages(bot, ids=m.id)
        print(f"Page {page} buttons:")
        for row in m.buttons:
            print("  ", [b.text for b in row])

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(inspect_pages())
