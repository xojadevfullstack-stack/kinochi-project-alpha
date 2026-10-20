import asyncio
import os
import sys
import json
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from telethon import TelegramClient
from telethon.sessions import StringSession

OLD_STORAGE = -1003926001543

SEARCHES = [
    # Cho'qintirgan ota
    ("godfather", ["cho'qintirgan", "godfather", "krestniy"]),
    # Labirint
    ("maze_runner", ["labirint"]),
    # Mumiya
    ("mummy", ["mumiya"]),
    # O'yinchoqlar tarixi
    ("toy_story", ["o'yinchoqlar tarixi", "oyinchoqlar", "toy story"]),
    # Arra (Saw)
    ("saw", ["arra"]),
    # Qichqiriq (Scream)
    ("scream", ["qichqiriq"]),
    # Conjuring / Astral / Annabel
    ("conjuring_universe", ["astral", "annabel", "la'nat", "lanat", "monaxinya"]),
    # Betmen klassik
    ("batman_classic", ["betmen", "batman"]),
    # Terminator qo'shimcha
    ("terminator_extra", ["terminator"]),
    # Jon Uik qo'shimcha
    ("john_wick_extra", ["balerina", "kontinental"]),
    # Spider-Man animations
    ("spiderman_anim", ["yondosh olam", "olamlar to'ri", "spider-man", "spider man", "o'rgimchak"]),
    # Yura davri
    ("jurassic", ["yura davri", "yura davriga", "jurassic"]),
    # Muzlik davri 6
    ("ice_age_extra", ["muzlik davri"]),
    # Shrek maxsus
    ("shrek_extra", ["shrek"]),
]

async def audit():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    found = {}

    for cat, terms in SEARCHES:
        found[cat] = []
        seen_ids = set()
        for term in terms:
            async for msg in client.iter_messages(OLD_STORAGE, search=term, limit=60):
                if msg.id in seen_ids:
                    continue
                seen_ids.add(msg.id)
                if msg.video or msg.document:
                    fn = ""
                    if msg.file and hasattr(msg.file, "name"):
                        fn = msg.file.name or ""
                    txt = (msg.message or "").replace("\n", " ")[:120]
                    found[cat].append({
                        "id": msg.id,
                        "date": str(msg.date),
                        "file_name": fn,
                        "text": txt
                    })

    await client.disconnect()

    with open("scripts/audit_results.json", "w", encoding="utf-8") as f:
        json.dump(found, f, ensure_ascii=False, indent=2)

    print("=== AUDIT RESULTS SUMMARY ===")
    for cat, items in found.items():
        print(f"\n[{cat.upper()}] ({len(items)} items)")
        for it in items[:8]:
            print(f"  ID {it['id']}: {it['file_name']} | {it['text'][:80]}")

if __name__ == "__main__":
    asyncio.run(audit())
