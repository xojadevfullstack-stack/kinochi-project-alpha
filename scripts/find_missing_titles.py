import asyncio
import os
import sys
import json
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

CHANNELS = [-1003926001543, -1003941035700]

TITLES = [
    ("Titanik", ["Titanik", "Titanic"]),
    ("Anora", ["Anora"]),
    ("Suzume", ["Suzume"]),
    ("Kiki", ["Kiki", "KIKI"]),
    ("Nafis so'zlar", ["Nafis so", "so'zlar bog'i", "suzlar bogi"]),
    ("Josee", ["Josee", "yo'lbars va baliq"]),
    ("Qora Pantera", ["Qora Pantera", "Black Panther"]),
    ("Arra 1", ["Arra 1", "Arra"]),
    ("Terminator 4", ["Terminator 4", "Najotkorning"]),
    ("Terminator 5", ["Terminator 5", "Genezis"]),
    ("Qashqirlar Iroq", ["Iroq", "Kurtlar Vadisi Irak"]),
    ("Muro", ["Muro", "Nalet Olsun"]),
    ("Akira", ["Akira"]),
    ("Bolakay", ["Bolakay", "ko'rsichqon"]),
    ("Sening oshqozon", ["Sening oshqozon", "oshqozon osti"]),
]

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    found = {}
    for name, queries in TITLES:
        found[name] = []
        for ch in CHANNELS:
            for q in queries:
                async for msg in client.iter_messages(ch, search=q, limit=10):
                    if msg.video or msg.document:
                        txt = (msg.message or "").replace("\n", " ")[:100]
                        if not any(x["id"] == msg.id for x in found[name]):
                            found[name].append({"id": msg.id, "ch": ch, "text": txt})
        print(f"[{name}] Found: {len(found[name])} matches")
        for m in found[name][:2]:
            print(f"   ID {m['id']} (ch {m['ch']}): {m['text'][:80]}")

    await client.disconnect()

    with open("scripts/found_missing_titles.json", "w", encoding="utf-8") as f:
        json.dump(found, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    asyncio.run(main())
