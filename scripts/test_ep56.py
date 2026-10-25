import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def test_ep56():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    bot = 'asilmediabot'
    # Start /start 11153
    sent = await client.send_message(bot, "/start 11153")
    await asyncio.sleep(2.5)

    card = None
    async for m in client.iter_messages(bot, limit=4):
        if m.id > sent.id and m.buttons:
            card = m
            break

    print("Card found:", card.id)
    # Page 3 has 56 (41-60)
    # Click next twice
    for p in range(2):
        # find '▶️'
        next_btn = next(((r, c) for r, row in enumerate(card.buttons) for c, b in enumerate(row) if '▶️' in b.text or '➡️' in b.text), None)
        if next_btn:
            print(f"Clicking next {p+1}...")
            await card.click(next_btn[0], next_btn[1])
            await asyncio.sleep(1.8)
            card = await client.get_messages(bot, ids=card.id)

    print("Card page 3 buttons:")
    for row in card.buttons:
        print(" ", [b.text for b in row])

    # Find button '56'
    btn_56 = next(((r, c) for r, row in enumerate(card.buttons) for c, b in enumerate(row) if b.text.strip() == '56'), None)
    if btn_56:
        print("Clicking button 56...")
        await card.click(btn_56[0], btn_56[1])
        await asyncio.sleep(3.5)
        async for reply in client.iter_messages(bot, limit=2):
            if reply.file:
                txt = (reply.text or "[No text]").replace("\n", " ")[:100]
                print(f"Reply: {reply.file.name} ({round(reply.file.size/1024/1024, 1)} MB) | {txt}")
                break

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_ep56())
