import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def search_asilmedia_channels():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    channels = [-1001154306049, -1001663313446]

    for ch_id in channels:
        ch = await client.get_entity(ch_id)
        print(f"\n==========================================")
        print(f"Searching channel: {ch.title} ({ch_id})")
        print(f"==========================================")

        for q in ["gladio", "muro", "pistirma", "pusu", "vatan", "iroq", "falastin"]:
            count = 0
            async for m in client.iter_messages(ch_id, search=q, limit=5):
                count += 1
                txt = (m.text or "[No text]").replace("\n", " ")[:100]
                has_file = bool(m.file)
                f_name = m.file.name if m.file else None
                f_size = round(m.file.size/1024/1024, 1) if m.file else 0
                print(f"  [{q}] Msg {m.id} | Has file: {has_file} ({f_name}, {f_size} MB) | Text: {txt}")
            if count == 0:
                print(f"  [{q}] 0 results")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(search_asilmedia_channels())
