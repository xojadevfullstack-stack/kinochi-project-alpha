import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def test_ep69_next():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    bot = 'asilmediabot'
    # Find card
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

    # Click button '69' (row 1, col 3)
    print("Clicking button 69...")
    await card.click(1, 3)
    await asyncio.sleep(3.5)

    msg_69 = None
    async for m in client.iter_messages(bot, limit=2):
        if m.file:
            msg_69 = m
            print(f"Msg 69: {m.file.name}")
            break

    if msg_69 and msg_69.buttons:
        print("Clicking 'Keyingi qism' on msg 69...")
        await msg_69.click(0, 0)
        await asyncio.sleep(3.5)
        async for m in client.iter_messages(bot, limit=2):
            if m.id > msg_69.id and m.file:
                print(f"Reply after 69: {m.file.name} | Text: {m.text[:100]}")
                break

    # Now let's test what button row 1, col 4 ('71') gives:
    print("\nClicking row 1, col 4 (button '71')...")
    card = await client.get_messages(bot, ids=card.id)
    await card.click(1, 4)
    await asyncio.sleep(3.5)
    async for m in client.iter_messages(bot, limit=2):
        if m.file:
            print(f"Button (1, 4) gives: {m.file.name} | Text: {m.text[:100]}")
            break

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_ep69_next())
