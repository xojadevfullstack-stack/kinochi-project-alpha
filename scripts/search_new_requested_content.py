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

from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text
from telethon import TelegramClient
from telethon.sessions import StringSession

TARGET_QUERIES = [
    # Movies / Franchises
    ("Cho'qintirgan ota", ["%cho'qintirgan%", "%choqintirgan%", "%godfather%"]),
    ("Labirint yuguruvchisi", ["%labirint%", "%maze runner%"]),
    ("Mumiya", ["%mumiya%", "%mummy%"]),
    ("O'yinchoqlar tarixi", ["%o'yinchoqlar%", "%oyinchoqlar%", "%toy story%"]),
    ("Arra (Saw)", ["%arra%", "%saw%"]),
    ("Qichqiriq (Scream)", ["%qichqiriq%", "%scream%"]),
    ("La'nat / Astral / Annabel", ["%la'nat%", "%lanat%", "%astral%", "%annabel%", "%conjuring%", "%insidious%"]),
    ("Betmen klassik", ["%betmen%", "%batman%"]),
    ("Terminator qo'shimcha", ["%terminator%"]),
    ("Jon Uik qo'shimcha", ["%balerina%", "%ballerina%", "%kontinental%", "%continental%"]),
    ("Yura davri parki / olami", ["%yura%", "%jurassic%"]),
    ("O'rgimchak animatsiya", ["%yondosh olam%", "%olamlar to'ri%", "%spider-verse%", "%spider verse%"]),
    ("Muzlik davri 6", ["%muzlik%"]),
    ("Shrek maxsus", ["%shrek%"]),
]

async def search_db():
    results = {}
    async with async_session_factory() as session:
        for name, patterns in TARGET_QUERIES:
            where_clauses = " OR ".join(["lower(title) LIKE :p" + str(i) + " OR lower(original_title) LIKE :p" + str(i) for i in range(len(patterns))])
            params = {f"p{i}": pat.lower() for i, pat in enumerate(patterns)}
            sql = f"SELECT id, title, original_title, release_year, tmdb_id, code, source_type, source_chat_id, source_topic_id, poster_url FROM movies WHERE {where_clauses}"
            res = await session.execute(text(sql), params)
            rows = res.fetchall()
            results[name] = []
            for r in rows:
                # translations
                t_res = await session.execute(text("SELECT id, language, storage_channel_message_id FROM movie_translations WHERE movie_id = :mid"), {"mid": r[0]})
                t_rows = t_res.fetchall()
                results[name].append({
                    "id": r[0],
                    "title": r[1],
                    "original_title": r[2],
                    "year": r[3],
                    "tmdb_id": r[4],
                    "code": r[5],
                    "source_type": r[6],
                    "source_topic_id": r[8],
                    "poster_url": r[9],
                    "translations": [(tr[0], tr[1], tr[2]) for tr in t_rows]
                })
    return results

async def search_telegram():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    OLD_STORAGE = -1003926001543
    tg_results = {}

    search_terms = [
        "cho'qintirgan", "godfather",
        "labirint", "maze runner",
        "mumiya", "mummy",
        "o'yinchoqlar", "toy story",
        "arra", "saw",
        "qichqiriq", "scream",
        "astral", "annabel", "la'nat", "conjuring", "insidious",
        "yura davri", "jurassic",
        "balerina", "kontinental",
        "yondosh olam", "olamlar to'ri"
    ]

    for term in search_terms:
        matches = []
        async for msg in client.iter_messages(OLD_STORAGE, search=term, limit=40):
            if msg.video or msg.document:
                txt = (msg.message or "").replace("\n", " ")[:120]
                doc_name = ""
                if msg.file and hasattr(msg.file, "name"):
                    doc_name = msg.file.name or ""
                matches.append({
                    "id": msg.id,
                    "date": str(msg.date),
                    "file_name": doc_name,
                    "text": txt
                })
        if matches:
            tg_results[term] = matches
            print(f"[TG SEARCH] '{term}': {len(matches)} ta topildi")

    await client.disconnect()
    return tg_results

async def main():
    print("--- 1. Searching Database ---")
    db_res = await search_db()
    for name, items in db_res.items():
        if items:
            print(f"[DB] {name}: {len(items)} ta")
            for it in items[:6]:
                print(f"   ID {it['id']}: {it['title']} ({it['year']}) TMDB:{it['tmdb_id']} Translations: {it['translations']}")

    print("\n--- 2. Searching Old Telegram Channel ---")
    tg_res = await search_telegram()

    with open("scripts/new_requested_search.json", "w", encoding="utf-8") as f:
        json.dump({"db": db_res, "tg": tg_res}, f, ensure_ascii=False, indent=2)

    print("\nNatijalar scripts/new_requested_search.json ga saqlandi!")

if __name__ == "__main__":
    asyncio.run(main())
