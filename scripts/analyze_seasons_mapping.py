import asyncio
import os
import sys
import re

sys.stdout.reconfigure(encoding='utf-8')
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

load_dotenv('.env.local')
load_dotenv('.env')

async def analyze_topic(client, old_chat, topic_id, name):
    print(f"\n=======================================================")
    print(f"PARSING TOPIC {topic_id}: {name}")
    print(f"=======================================================")
    
    videos = []
    codes = {}
    
    async for m in client.iter_messages(old_chat, reply_to=topic_id, reverse=True):
        if m.video or (m.document and m.file and m.file.mime_type and m.file.mime_type.startswith('video/')):
            videos.append(m)
        elif m.text:
            # Check for code like S1-CH1 or S2-CH5
            match = re.search(r"S(\d+)[\-_]CH(\d+)", m.text, re.IGNORECASE)
            if match:
                s_num = int(match.group(1))
                ep_num = int(match.group(2))
                # Also check which message it replied to or if sequential
                codes[m.id] = (s_num, ep_num, m.reply_to.reply_to_msg_id if m.reply_to else None)

    print(f"Total videos: {len(videos)}")
    print(f"Total code texts: {len(codes)}")
    
    # Let's inspect season groupings
    seasons = {}
    for code_id, (s_num, ep_num, rep_id) in codes.items():
        seasons.setdefault(s_num, []).append((ep_num, rep_id))
    
    for s_num in sorted(seasons.keys()):
        eps = seasons[s_num]
        print(f"  Season {s_num}: {len(eps)} episodes (min ep: {min(e[0] for e in eps)}, max ep: {max(e[0] for e in eps)})")

async def main():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    old_chat = -1003941035700
    
    await analyze_topic(client, old_chat, 317, "Ajdar xonadoni (House of the Dragon)")
    await analyze_topic(client, old_chat, 3665, "Yigitlar (The Boys)")
    await analyze_topic(client, old_chat, 957, "Mashaqqatlar sari (Breaking Bad)")
    await analyze_topic(client, old_chat, 5392, "Haqiqiylar (The Originals)")
    await analyze_topic(client, old_chat, 2876, "Yosh bo'ri (Teen Wolf)")
    await analyze_topic(client, old_chat, 1195, "Vampir kundaligi (The Vampire Diaries)")
    
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
