import asyncio
import os
import json
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

BASE_DIR = r"c:\Users\Администратор\Desktop\kino bot project\kinochi project"
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

SEARCH_TERMS = [
    # Series
    ("Qochqin (Prison Break)", ["Qochqin", "Prison Break"]),
    ("O'tkir soyabonlar (Peaky Blinders)", ["O'tkir soyabonlar", "Peaky Blinders", "Otkir soyabonlar"]),
    ("Qing'ir ishlar (Breaking Bad)", ["Qing'ir ishlar", "Breaking Bad", "Qingir ishlar"]),
    ("Better Call Saul", ["Better Call Saul", "Solga qo'ng'iroq", "Solga qongiroq"]),
    ("Sherlok", ["Sherlok", "Sherlock"]),
    ("G'aroyib ishlar (Stranger Things)", ["G'aroyib ishlar", "Stranger Things", "Garoyib ishlar"]),
    ("Kalmar o'yini (Squid Game)", ["Kalmar o'yini", "Squid Game", "Kalmar oyini"]),
    ("Hamma o'liklar maktabi (All of Us Are Dead)", ["Hamma o'liklar", "All of Us Are Dead"]),
]

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    channels = [-1003941035700, -1003926001543]
    summary = {}

    for label, queries in SEARCH_TERMS:
        summary[label] = {}
        for ch_id in channels:
            matched = []
            for q in queries:
                async for msg in client.iter_messages(ch_id, search=q, limit=20):
                    if not any(m["id"] == msg.id for m in matched):
                        media_type = type(msg.media).__name__ if msg.media else None
                        text_p = (msg.message or "")[:120].replace("\n", " ")
                        matched.append({"id": msg.id, "media": media_type, "text": text_p})
            summary[label][str(ch_id)] = matched

    with open("scripts/series_search_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print("Summary written to scripts/series_search_summary.json")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
