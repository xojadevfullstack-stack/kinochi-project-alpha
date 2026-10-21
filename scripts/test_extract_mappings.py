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

async def extract_topic_episodes(client, old_chat, topic_id):
    all_msgs = []
    async for m in client.iter_messages(old_chat, reply_to=topic_id, reverse=True):
        all_msgs.append(m)

    # Find videos and codes
    video_msgs = [m for m in all_msgs if m.video or (m.document and m.file and m.file.mime_type and m.file.mime_type.startswith('video/'))]
    
    code_msgs = []
    for m in all_msgs:
        if m.text:
            match = re.search(r"S(\d+)[\-_]CH(\d+)", m.text, re.IGNORECASE)
            if match:
                s_num = int(match.group(1))
                ep_num = int(match.group(2))
                code_msgs.append((m.id, s_num, ep_num))

    print(f"Topic {topic_id}: {len(video_msgs)} videos, {len(code_msgs)} codes")
    
    # Check if count matches
    mapping = {}
    if len(video_msgs) == len(code_msgs):
        for v, (_, s_num, ep_num) in zip(video_msgs, code_msgs):
            mapping.setdefault(s_num, []).append((ep_num, v.id))
    else:
        print(f"Warning: video count ({len(video_msgs)}) != code count ({len(code_msgs)}) in topic {topic_id}")
        # Let's inspect
        for idx in range(min(5, len(video_msgs))):
            print(f"  V[{idx}]: ID {video_msgs[idx].id} | Code: {code_msgs[idx] if idx < len(code_msgs) else 'None'}")

    for s_num in sorted(mapping.keys()):
        eps = mapping[s_num]
        print(f"  Mapped Season {s_num}: {len(eps)} eps (ID {eps[0][1]} to {eps[-1][1]})")

    return mapping

async def main():
    api_id = int(os.getenv('TELEGRAM_API_ID'))
    api_hash = os.getenv('TELEGRAM_API_HASH')
    session_str = os.getenv('TELEGRAM_STRING_SESSION')
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    old_chat = -1003941035700
    
    print("--- 317: House of the Dragon ---")
    await extract_topic_episodes(client, old_chat, 317)
    
    print("\n--- 3665: The Boys ---")
    await extract_topic_episodes(client, old_chat, 3665)
    
    print("\n--- 957: Breaking Bad ---")
    await extract_topic_episodes(client, old_chat, 957)
    
    print("\n--- 5392: The Originals ---")
    await extract_topic_episodes(client, old_chat, 5392)
    
    print("\n--- 2876: Teen Wolf ---")
    await extract_topic_episodes(client, old_chat, 2876)
    
    print("\n--- 1195: The Vampire Diaries ---")
    await extract_topic_episodes(client, old_chat, 1195)

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
