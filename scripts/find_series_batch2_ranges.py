import asyncio
import os
import sys
import json
import re
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

CH1 = -1003926001543
CH2 = -1003941035700

TARGET_QUERIES = {
    "vampire_diaries": ["Vampirlar kundaligi", "s_39", "The Vampire Diaries"],
    "originals": ["The Originals", "Haqiqiylar", "s_92", "Asllar"],
    "last_kingdom": ["So'nggi qirollik", "Soʻnggi qirollik", "The Last Kingdom", "s_45"],
    "superman_lois": ["Supermen va Lois", "Superman & Lois", "Supermen va Lois serial"],
    "jessica_jones": ["Jessika Jons", "Jessica Jones"],
    "death_note": ["O'lim kundaligi", "Oʻlim kundaligi", "Death Note"],
    "solo_leveling": ["Yolg'izlikda daraja", "Yolgʻizlikda daraja", "Solo Leveling"],
    "one_piece": ["Van Pis", "One Piece", "Qaroqchilar qiroli"],
    "naruto": ["Naruto"],
    "bleach": ["Bleach", "Oqartiruvchi"],
    "kurtlar_vadisi_asl": ["Qashqirlar makoni (Asl", "Aslan Akbey", "Polat Alemdar"],
    "kurtlar_pusu": ["Kurtlar Vadisi: Pusu", "Qashqirlar makoni: Pistirma", "Pistirma"]
}

async def scan():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    results = {}

    for name, queries in TARGET_QUERIES.items():
        found = {}
        for q in queries:
            for ch in [CH1, CH2]:
                try:
                    async for msg in client.iter_messages(ch, search=q, limit=200):
                        if not (msg.video or msg.document):
                            continue
                        if msg.id in found:
                            continue
                        txt = msg.message or ""
                        found[msg.id] = {
                            "id": msg.id,
                            "ch": ch,
                            "text": txt[:80].replace("\n", " ")
                        }
                except Exception as e:
                    print(f"Error searching '{q}' in {ch}: {e}")
        results[name] = list(found.values())
        print(f"[{name}]: found {len(found)} video messages")

    await client.disconnect()

    with open("scripts/found_series_batch2.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("Scan completed! Saved to scripts/found_series_batch2.json")

if __name__ == "__main__":
    asyncio.run(scan())
