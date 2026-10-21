import asyncio
import os
import sys
import json

sys.stdout.reconfigure(encoding='utf-8')
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('.env')

async def main():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    
    old_chat = -1003941035700
    all_msgs = []
    async for m in client.iter_messages(old_chat, reply_to=525, reverse=True):
        all_msgs.append(m)

    print(f"Total msgs: {len(all_msgs)}")
    videos = []
    texts = []
    
    for m in all_msgs:
        is_video = m.video or (m.document and m.file and m.file.mime_type and m.file.mime_type.startswith('video/'))
        if is_video:
            videos.append(m)
        elif m.text and 'saqlandi va indekslandi' in m.text:
            texts.append(m)

    print(f"Total videos: {len(videos)}")
    print(f"Total index texts: {len(texts)}")

    # Let's inspect all video IDs
    print("\n--- All Videos ---")
    for idx, v in enumerate(videos, start=1):
        f_name = getattr(v.file, 'name', '')
        size_mb = round(v.file.size / (1024*1024), 1) if v.file else 0
        print(f"{idx:02d}. ID: {v.id} | Size: {size_mb} MB | Name: {f_name}")

    print("\n--- All Index Texts ---")
    for idx, t in enumerate(texts, start=1):
        print(f"{idx:02d}. ID: {t.id} | Text: {t.text}")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
