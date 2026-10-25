import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os, re
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def check_seasons_distribution():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    old_chat = -1003941035700
    topic_id = 33418

    seasons = {}
    async for m in client.iter_messages(old_chat, reply_to=topic_id):
        if m.file and m.text:
            m_s = re.search(r'(\d+)\s*[-_]?\s*(?:mavsum|fasl|season)', m.text, re.I)
            m_e = re.search(r'(\d+)\s*[-_]?\s*qism', m.text, re.I)
            s_num = int(m_s.group(1)) if m_s else 1
            e_num = int(m_e.group(1)) if m_e else None
            if e_num:
                if s_num not in seasons:
                    seasons[s_num] = []
                seasons[s_num].append(e_num)

    for s_num in sorted(seasons.keys()):
        eps = sorted(seasons[s_num])
        print(f"Season {s_num}: {len(eps)} eps (from {eps[0]} to {eps[-1]})")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check_seasons_distribution())
