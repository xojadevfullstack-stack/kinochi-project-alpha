import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def test_films():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    bot = 'asilmediabot'

    for idx, film_name in [(0, "Iroq (2006)"), (2, "Vatan (2017)"), (3, "Falastin (2011)")]:
        print(f"\n==========================================")
        print(f"Testing {film_name} (Row {idx})")
        print(f"==========================================")
        sent = await client.send_message(bot, "qashqirlar makoni")
        await asyncio.sleep(3.0)

        res_msg = None
        async for m in client.iter_messages(bot, limit=5):
            if m.id > sent.id and m.buttons:
                res_msg = m
                break

        if not res_msg:
            print("No search result!")
            continue

        print(f"Clicking row {idx}: {res_msg.buttons[idx][0].text}")
        await res_msg.click(idx, 0)
        await asyncio.sleep(4.0)

        async for m in client.iter_messages(bot, limit=4):
            if m.id > res_msg.id:
                txt = (m.text or "[No text]").replace("\n", " ")[:120]
                print(f"Msg {m.id} | Has file: {bool(m.file)} | Text: {txt}")
                if m.buttons:
                    print("  Buttons:")
                    for r in m.buttons:
                        print("   ", [b.text for b in r])

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test_films())
