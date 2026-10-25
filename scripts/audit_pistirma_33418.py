import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os, re
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def audit_pistirma_33418():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    old_chat = -1003941035700
    topic_id = 33418

    episodes = {}
    async for m in client.iter_messages(old_chat, reply_to=topic_id):
        if m.file and m.text:
            m_s = re.search(r'(\d+)\s*[-_]?\s*(?:mavsum|fasl|season)', m.text, re.I)
            m_e = re.search(r'(\d+)\s*[-_]?\s*qism', m.text, re.I)
            season = int(m_s.group(1)) if m_s else 1
            ep = int(m_e.group(1)) if m_e else None
            if ep:
                episodes[ep] = (m.id, season)

    print(f"Total parsed episodes in topic 33418: {len(episodes)}")
    missing = [e for e in range(1, 301) if e not in episodes]
    print(f"Missing episodes out of 1-300: {len(missing)}")
    if missing:
        print("  Missing list:", missing[:20])
    else:
        print("  ALL 300 EPISODES ARE 100% PRESENT IN TOPIC 33418!")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(audit_pistirma_33418())
