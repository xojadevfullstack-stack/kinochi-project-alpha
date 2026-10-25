import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
import asyncio, os
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('backend/.env')

async def check_old_channel_qashqirlar():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    old_chat = -1003941035700
    print("Searching old channel for 'qashqirlar'...")
    found_topics = []
    async for m in client.iter_messages(old_chat, search="qashqirlar", limit=15):
        reply_to_top = getattr(m, 'reply_to_top_id', None) or (m.reply_to.reply_to_top_id if m.reply_to and hasattr(m.reply_to, 'reply_to_top_id') else None)
        reply_to_msg = getattr(m, 'reply_to_msg_id', None) or (m.reply_to.reply_to_msg_id if m.reply_to else None)
        topic_id = reply_to_top or reply_to_msg
        txt = (m.text or "[No text]").replace("\n", " ")[:100]
        print(f"Msg {m.id} | Topic: {topic_id} | Text: {txt}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(check_old_channel_qashqirlar())
