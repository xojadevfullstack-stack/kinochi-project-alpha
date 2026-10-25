import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def check_p4():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    bot = 'asilmediabot'
    sent = await client.send_message(bot, "/start 11153")
    await asyncio.sleep(2.5)

    card = None
    async for m in client.iter_messages(bot, limit=4):
        if m.id > sent.id and m.buttons:
            card = m
            break

    # Go to page 4
    for _ in range(3):
        next_p = next(((r, c) for r, row in enumerate(card.buttons) for c, b in enumerate(row) if "▶️" in b.text or "➡️" in b.text), None)
        if next_p:
            await card.click(next_p[0], next_p[1])
            await asyncio.sleep(1.8)
            card = await client.get_messages(bot, ids=card.id)

    print("Page 4 buttons:")
    for row in card.buttons:
        print(" ", [b.text for b in row])

    # Also go to page 5
    next_p = next(((r, c) for r, row in enumerate(card.buttons) for c, b in enumerate(row) if "▶️" in b.text or "➡️" in b.text), None)
    if next_p:
        await card.click(next_p[0], next_p[1])
        await asyncio.sleep(1.8)
        card = await client.get_messages(bot, ids=card.id)

    print("\nPage 5 buttons:")
    for row in card.buttons:
        print(" ", [b.text for b in row])

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check_p4())
