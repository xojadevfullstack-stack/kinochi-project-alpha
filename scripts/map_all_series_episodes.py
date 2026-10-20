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

OLD_STORAGE = -1003926001543

SERIES_QUERIES = {
    "the_boys": ["Yigitlar (The Boys)", "The Boys", "Yigitlar"],
    "breaking_bad": ["Mashaqqatlar sari", "Breaking Bad"],
    "prison_break": ["Panjara ortida", "Prison Break"],
    "vikings": ["Vikinglar", "Vikings"],
    "teen_wolf": ["Yosh bo'ri", "Yosh boʻri", "Teen Wolf"],
    "sherlock": ["Sherlok", "Sherlock"],
    "dark": ["Zulmat", "Dark"],
    "witcher": ["Jodugar (The Witcher)", "Jodugar"],
    "mentalist": ["Ruxshunos", "Mentalist"],
    "all_of_us_are_dead": ["Barchamiz o'likmiz", "Barchamiz oʻlikmiz", "All of Us Are Dead"],
    "continental": ["Kontinental", "Continental"],
    "percy_jackson": ["Persi Jekson", "Percy Jackson"],
    "daredevil": ["Daredevil", "Qo'rqmas"],
    "shield": ["Qalqon Agentlari", "Agents of S.H.I.E.L.D."],
    "reacher": ["Jek Richer", "Reacher"],
    "the_strain": ["Shtamm", "The Strain"],
    "attack_on_titan": ["Titanlar hujumi", "Attack on Titan"],
    "death_note": ["O'lim kundaligi", "Oʻlim kundaligi", "Death Note"],
    "jujutsu_kaisen": ["Jodugarlar jangi", "Jujutsu Kaisen"],
    "solo_leveling": ["Yolg'izlikda daraja", "Yolgʻizlikda daraja", "Solo Leveling"],
    "kurtlar_pusu": ["Pistirma", "Kurtlar Vadisi: Pusu"],
    "kurtlar_asl": ["Qashqirlar makoni", "Kurtlar Vadisi"]
}

async def scan():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    results = {}

    for key, terms in SERIES_QUERIES.items():
        found = {}
        for term in terms:
            async for msg in client.iter_messages(OLD_STORAGE, search=term, limit=120):
                if not (msg.video or msg.document):
                    continue
                if msg.id in found:
                    continue
                txt = msg.message or ""
                # parse season & episode if present
                m = re.search(r'(\d+)\s*[-_]?\s*mavsum.*?(\d+)\s*[-_]?\s*qism', txt, re.IGNORECASE)
                s_num, ep_num = None, None
                if m:
                    s_num, ep_num = int(m.group(1)), int(m.group(2))
                else:
                    m2 = re.search(r'S(\d+)[-_]CH(\d+)', txt, re.IGNORECASE)
                    if m2:
                        s_num, ep_num = int(m2.group(1)), int(m2.group(2))
                found[msg.id] = {
                    "id": msg.id,
                    "date": str(msg.date),
                    "season": s_num,
                    "episode": ep_num,
                    "text": txt[:100].replace('\n', ' ')
                }
        results[key] = list(found.values())
        print(f"[{key}]: found {len(found)} videos")

    await client.disconnect()

    with open("scripts/mapped_series_episodes.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("Saved to scripts/mapped_series_episodes.json")

if __name__ == "__main__":
    asyncio.run(scan())
