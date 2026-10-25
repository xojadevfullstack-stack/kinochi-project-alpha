import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def inspect_asilmedia_qashqirlar():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    bot = 'asilmediabot'
    sent = await client.send_message(bot, "qashqirlar makoni")
    await asyncio.sleep(3.0)

    # find the search result msg
    res_msg = None
    async for m in client.iter_messages(bot, limit=5):
        if m.id > sent.id and m.buttons:
            res_msg = m
            break

    if not res_msg:
        print("No search result message!")
        await client.disconnect()
        return

    print("Found search result:")
    for row_idx, row in enumerate(res_msg.buttons):
        for col_idx, b in enumerate(row):
            print(f"Row {row_idx}, Col {col_idx}: '{b.text}'")

    # Let's inspect 'Qashqirlar Makoni (2003)' (the series)
    # It is row 1
    print("\nClicking 'Qashqirlar Makoni (2003)'...")
    click_res = await res_msg.click(1, 0)
    await asyncio.sleep(4.0)

    async for m in client.iter_messages(bot, limit=4):
        txt = (m.text or "[No text]").replace("\n", " ")[:150]
        print(f"Msg {m.id} | Has file: {bool(m.file)} | Text: {txt}")
        if m.buttons:
            print("  Buttons:")
            for r in m.buttons:
                print("   ", [btn.text for btn in r])

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(inspect_asilmedia_qashqirlar())
