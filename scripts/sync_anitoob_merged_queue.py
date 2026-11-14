import os
import sys
import json
import re
import asyncio
from typing import List, Dict, Any, Tuple

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.infrastructure.db.session import async_session_factory
from sqlalchemy import text
from app.infrastructure.external.tmdb_client import TMDbClient

SCRATCH_DIR = "C:/Users/Администратор/.gemini/antigravity/brain/46c98ace-bf0a-4138-8af3-4b50291d3adf/scratch"
FULL_LIST_PATH = os.path.join(SCRATCH_DIR, "anitoob_full_list.json")

# Verified franchise definitions (High priority order)
FRANCHISE_MAP = {
    "my_hero_academia": {
        "tmdb_id": 65930,
        "canonical_title": "My Hero Academia",
        "items": [
            {"code": "227", "season": 1, "title": "Mening qahramonlik akademiyam (1-mavsum)"},
            {"code": "228", "season": 2, "title": "Mening qahramonlik akademiyam (2-mavsum)"},
            {"code": "229", "season": 3, "title": "Mening qahramonlik akademiyam (3-mavsum)"},
            {"code": "230", "season": 4, "title": "Mening qahramonlik akademiyam (4-mavsum)"},
            {"code": "231", "season": 5, "title": "Mening qahramonlik akademiyam (5-mavsum)"},
            {"code": "234", "season": 6, "title": "Mening qahramonlik akademiyam (6-mavsum)"},
        ]
    },
    "naruto": {
        "canonical_title": "Naruto",
        "items": [
            {"code": "78", "season": 1, "tmdb_id": 46260, "media_type": "anime", "title": "Naruto (1-fasil)"},
            {"code": "206", "season": 2, "tmdb_id": 31910, "media_type": "anime", "title": "Naruto: Shippuden (2-fasil)"},
            {"code": "90", "tmdb_id": 124449, "media_type": "movie", "title": "Naruto 8-film: Qonli qamoqxona"},
            {"code": "296", "tmdb_id": 140700, "media_type": "movie", "title": "Naruto 9-film: Ninjalik yo'li"},
        ]
    },
    "jujutsu_kaisen": {
        "canonical_title": "Jujutsu Kaisen",
        "items": [
            {"code": "28", "season": 1, "tmdb_id": 95479, "media_type": "anime", "title": "Jodugarlar jangi (1-mavsum)"},
            {"code": "29", "season": 2, "tmdb_id": 95479, "media_type": "anime", "title": "Jodugarlar jangi (2-mavsum)"},
            {"code": "30", "season": 3, "tmdb_id": 95479, "media_type": "anime", "title": "Jodugarlar jangi (3-mavsum)"},
            {"code": "56", "tmdb_id": 810693, "media_type": "movie", "title": "Jodugarlar jangi 0 (Film)"},
        ]
    },
    "attack_on_titan": {
        "canonical_title": "Attack on Titan",
        "items": [
            {"code": "100", "season": 1, "tmdb_id": 1429, "media_type": "anime", "title": "Titanlar hujumi (1-4 fasllar)"},
        ]
    },
    "chainsaw_man": {
        "canonical_title": "Chainsaw Man",
        "items": [
            {"code": "103", "season": 1, "tmdb_id": 114410, "media_type": "anime", "title": "Arra odam (1-mavsum)"},
            {"code": "11", "tmdb_id": 1218925, "media_type": "movie", "title": "Arra odam: Reze Arc (Film)"},
        ]
    },
    "slime": {
        "tmdb_id": 82540,
        "canonical_title": "That Time I Got Reincarnated as a Slime",
        "items": [
            {"code": "218", "season": 4, "title": "Shilliq sifatida qayta tug'ilganim haqida (4-mavsum)"},
        ]
    },
    "re_zero": {
        "tmdb_id": 65942,
        "canonical_title": "Re:ZERO -Starting Life in Another World-",
        "items": [
            {"code": "54", "season": 1, "title": "Re:Zero - Boshqa dunyoda hayot (1-3 mavsumlar)"},
            {"code": "161", "season": 4, "title": "Re:Zero - Boshqa dunyoda hayot (4-mavsum)"},
        ]
    },
    "demon_slayer": {
        "canonical_title": "Demon Slayer: Kimetsu no Yaiba",
        "items": [
            {"code": "41", "season": 1, "tmdb_id": 85937, "media_type": "anime", "title": "Iblislar qotili (1-5 mavsumlar)"},
            {"code": "20", "tmdb_id": 85937, "media_type": "movie", "title": "Iblislar qotili (Film)"},
        ]
    },
    "oshi_no_ko": {
        "tmdb_id": 203737,
        "canonical_title": "Oshi no Ko",
        "items": [
            {"code": "39", "season": 1, "title": "Yulduz farzandlari (1-2 mavsumlar)"},
            {"code": "73", "season": 3, "title": "Yulduz farzandlari (3-mavsum)"},
        ]
    },
    "jigokuraku": {
        "tmdb_id": 122226,
        "canonical_title": "Hell's Paradise",
        "items": [
            {"code": "35", "season": 1, "title": "Jahannam jannati (1-mavsum)"},
            {"code": "64", "season": 2, "title": "Jahannam jannati (2-mavsum)"},
        ]
    },
    "blue_lock": {
        "canonical_title": "Blue Lock",
        "items": [
            {"code": "82", "season": 1, "tmdb_id": 124800, "media_type": "anime", "title": "Ko'k zindon (1-2 mavsumlar)"},
            {"code": "114", "tmdb_id": 1160164, "media_type": "movie", "title": "Ko'k zindon: Nagi epizodi (Film)"},
        ]
    },
    "bleach": {
        "canonical_title": "Bleach",
        "items": [
            {"code": "44", "season": 1, "tmdb_id": 30984, "media_type": "anime", "title": "Bleach (Asosiy serial)"},
            {"code": "148", "season": 1, "tmdb_id": 209867, "media_type": "anime", "title": "Bleach: Ming yillik qonli urush"},
        ]
    },
    "solo_leveling": {
        "tmdb_id": 209867,
        "canonical_title": "Solo Leveling",
        "items": [
            {"code": "32", "season": 1, "title": "Yolg'izlikda daraja ko'tarish (1-mavsum)"},
            {"code": "33", "season": 2, "title": "Yolg'izlikda daraja ko'tarish (2-mavsum)"},
        ]
    },
    "iruma_kun": {
        "tmdb_id": 91801,
        "canonical_title": "Welcome to Demon School! Iruma-kun",
        "items": [
            {"code": "101", "season": 1, "title": "Iblislar maktabiga xush kelibsiz Iruma-kun (1-2 fasl)"},
            {"code": "192", "season": 4, "title": "Iblislar maktabiga xush kelibsiz Iruma-kun (4-fasl)"},
        ]
    },
    "angel_next_door": {
        "tmdb_id": 141071,
        "canonical_title": "The Angel Next Door Spoils Me Rotten",
        "items": [
            {"code": "144", "season": 1, "title": "Qo'shni farishta (1-mavsum)"},
        ]
    },
    "sword_art_online": {
        "tmdb_id": 45782,
        "canonical_title": "Sword Art Online",
        "items": [
            {"code": "12", "season": 1, "title": "Qilich san'ati online (1-4 fasllar)"},
        ]
    },
    "date_a_live": {
        "tmdb_id": 45763,
        "canonical_title": "Date A Live",
        "items": [
            {"code": "48", "season": 1, "title": "Jonli sana (1-5 mavsumlar)"},
        ]
    },
    "konosuba": {
        "tmdb_id": 65334,
        "canonical_title": "KonoSuba: God's Blessing on this Wonderful World!",
        "items": [
            {"code": "26", "season": 1, "title": "Bu ajoyib dunyo (1-3 fasllar)"},
        ]
    },
    "classroom_elite": {
        "tmdb_id": 71859,
        "canonical_title": "Classroom of the Elite",
        "items": [
            {"code": "174", "season": 4, "title": "Elita sinfi (4-fasl)"},
        ]
    },
    "violet_evergarden": {
        "tmdb_id": 74130,
        "canonical_title": "Violet Evergarden",
        "items": [
            {"code": "141", "season": 1, "title": "Violet Evergarden (Serial va Film)"},
        ]
    },
}

# Duplicate / redundant cards that should be marked already_exists
DUPLICATE_CARDS = {
    "203": "100",  # Titanlar Hujumi (dup of 100)
    "204": "103",  # Arra Odam (dup of 103)
    "143": "144",  # Qòshni farishta (dup of 144)
    "290": "210",  # Qora qirolning qaytishi
    "280": "240",  # Sinfsiz qahramon
    "258": "163",  # Another
    "250": "241",  # Mabud minorasi
    "226": "225",  # SEVGI OʻLIM VA ROBITLAR
    "122": "121",  # Qayta tuğilgan aristokratning misli kòrilmagan sarguzashtlari
}

# Standalone specific mappings
KNOWN_STANDALONE = {
    "1": {"tmdb_id": 100565, "title": "Eighty Six (86)", "media_type": "anime"},
    "2": {"tmdb_id": 99797, "title": "Gleipnir", "media_type": "anime"},
    "3": {"tmdb_id": 103546, "title": "Tonikawa: Over the Moon for You (Meni oyga olib ket)", "media_type": "anime"},
    "4": {"tmdb_id": 31356, "title": "Fullmetal Alchemist: Brotherhood (Metal alximik)", "media_type": "anime"},
    "5": {"tmdb_id": 113988, "title": "Platinum End (Platina yakun)", "media_type": "anime"},
    "6": {"tmdb_id": 74313, "title": "Inuyashiki: Last Hero", "media_type": "anime"},
    "7": {"tmdb_id": 39483, "title": "The Future Diary (Kelajak kundaligi)", "media_type": "anime"},
    "8": {"tmdb_id": 568160, "title": "Weathering with You (Tabiat farzandi)", "media_type": "movie"},
    "9": {"tmdb_id": 43818, "title": "Hyouka", "media_type": "anime"},
    "13": {"tmdb_id": 207347, "title": "Kaiju No. 8", "media_type": "anime"},
    "14": {"tmdb_id": 15999, "title": "Vampire Hunter D: Bloodlust", "media_type": "movie"},
    "15": {"tmdb_id": 13916, "title": "Death Note (O'lim daftari)", "media_type": "anime"},
    "16": {"tmdb_id": 917496, "title": "The Tunnel to Summer (Yozgi Urushima tuneli)", "media_type": "movie"},
    "17": {"tmdb_id": 591086, "title": "Hello World (Salom dunyo)", "media_type": "movie"},
    "18": {"tmdb_id": 158415, "title": "NieR:Automata Ver1.1a", "media_type": "anime"},
    "23": {"tmdb_id": 94605, "title": "Arcane", "media_type": "anime"},
    "25": {"tmdb_id": 204541, "title": "Heavenly Delusion (Jannat sarobi)", "media_type": "anime"},
    "27": {"tmdb_id": 61733, "title": "The Seven Deadly Sins (Yetti o'lim gunohlari)", "media_type": "anime"},
    "36": {"tmdb_id": 643586, "title": "A Whisker Away (Mushuk niqobi)", "media_type": "movie"},
    "38": {"tmdb_id": 118956, "title": "The Eminence in Shadow (Soyada ko'tarilish)", "media_type": "anime"},
    "43": {"tmdb_id": 378064, "title": "A Silent Voice (Ovoz shakli)", "media_type": "movie"},
    "47": {"tmdb_id": 73223, "title": "Black Clover (Qora klever)", "media_type": "anime"},
    "50": {"tmdb_id": 37854, "title": "One Piece", "media_type": "anime"},
    "55": {"tmdb_id": 239770, "title": "Dandadan", "media_type": "anime"},
    "59": {"tmdb_id": 61663, "title": "Your Lie in April (Aprel yolg'oni)", "media_type": "anime"},
    "60": {"tmdb_id": 218230, "title": "Zom 100: Bucket List of the Dead", "media_type": "anime"},
    "61": {"tmdb_id": 504253, "title": "I Want to Eat Your Pancreas", "media_type": "movie"},
    "63": {"tmdb_id": 209867, "title": "Frieren: Beyond Journey's End", "media_type": "anime"},
    "69": {"tmdb_id": 83095, "title": "Vinland Saga", "media_type": "anime"},
    "76": {"tmdb_id": 83097, "title": "Dororo", "media_type": "anime"},
    "77": {"tmdb_id": 34768, "title": "Kimi ni Todoke (Senga intilib)", "media_type": "anime"},
    "80": {"tmdb_id": 67075, "title": "Mob Psycho 100", "media_type": "anime"},
    "86": {"tmdb_id": 149870, "title": "The Wind Rises (Shamol ko'tariladi)", "media_type": "movie"},
    "163": {"tmdb_id": 43538, "title": "Another", "media_type": "anime"},
    "182": {"tmdb_id": 103768, "title": "Sen uchun O'lmas (To Your Eternity)", "media_type": "anime"},
    "199": {"tmdb_id": 205663, "title": "O'zga dunyoda fermerlik hayotim (Farming Life in Another World)", "media_type": "anime"},
    "202": {"tmdb_id": 215446, "title": "Egzartist boshqa dunyoda qayta tug'ilib eng kuchli bo'lishga intiladi", "media_type": "anime"},
    "207": {"tmdb_id": 223365, "title": "Wind Breaker: Shamolni bo'ysindirish", "media_type": "anime"},
    "208": {"tmdb_id": 242095, "title": "Sehrgar qizning ustaxonasi", "media_type": "anime"},
    "210": {"tmdb_id": 235123, "title": "Qora qirolning qaytishi", "media_type": "anime"},
    "212": {"tmdb_id": 1241982, "title": "Orqaga qara (Look Back)", "media_type": "movie"},
    "216": {"tmdb_id": 209867, "title": "Iblislar bazmi", "media_type": "anime"},
    "217": {"tmdb_id": 240411, "title": "Tayoq va qilich (Wistoria: Wand and Sword)", "media_type": "anime"},
    "224": {"tmdb_id": 216390, "title": "Yozakura oilasi (Mission: Yozakura Family)", "media_type": "anime"},
    "225": {"tmdb_id": 86831, "title": "Sevgi, o'lim va robotlar (Love, Death & Robots)", "media_type": "anime"},
    "241": {"tmdb_id": 99797, "title": "Mabud minorasi (Tower of God)", "media_type": "anime"},
}

async def sync():
    with open(FULL_LIST_PATH, "r", encoding="utf-8") as f:
        raw_items = json.load(f)
    items_by_code = {str(it.get("id")): it for it in raw_items}
    print(f"Loaded {len(raw_items)} items from anitoob_full_list.json")

    handled_codes = set()
    records_to_sync = []
    priority_counter = 2000  # Start high for top franchises

    # 1. Process Franchises first (ordered by seasons)
    for f_key, f_data in FRANCHISE_MAP.items():
        f_items = f_data.get("items", [])
        for sub_item in f_items:
            c = str(sub_item["code"])
            handled_codes.add(c)
            raw = items_by_code.get(c, {})
            title = sub_item.get("title") or raw.get("nom") or f"Anime #{c}"
            tmdb_id = sub_item.get("tmdb_id") or f_data.get("tmdb_id")
            media_type = sub_item.get("media_type") or f_data.get("media_type") or "anime"
            year_val = None
            try:
                if raw.get("yili") and str(raw.get("yili")).isdigit():
                    year_val = int(raw.get("yili"))
            except:
                pass
            ep_count = None
            try:
                if raw.get("qismi") and str(raw.get("qismi")).isdigit():
                    ep_count = int(raw.get("qismi"))
            except:
                pass

            payload = {
                "season_number": sub_item.get("season", 1),
                "franchise": f_key,
                "episodes_count": ep_count,
                "verified": bool(tmdb_id),
                "canonical_title": f_data.get("canonical_title"),
            }
            records_to_sync.append({
                "source": "anitoob",
                "source_id": c,
                "title": title,
                "original_title": f_data.get("canonical_title"),
                "year": year_val,
                "media_type": media_type,
                "url": f"https://t.me/ANITOOBUZ_BOT?start={c}",
                "poster_url": raw.get("image"),
                "status": "queued",
                "reason": None,
                "attempts": 0,
                "tmdb_id": tmdb_id,
                "priority": priority_counter,
                "payload": payload,
            })
            priority_counter -= 1

    print(f"Mapped {len(records_to_sync)} franchise items.")

    # 2. Process Duplicates (set already_exists)
    for dup_code, parent_code in DUPLICATE_CARDS.items():
        if dup_code in handled_codes:
            continue
        handled_codes.add(dup_code)
        raw = items_by_code.get(dup_code, {})
        records_to_sync.append({
            "source": "anitoob",
            "source_id": dup_code,
            "title": raw.get("nom", f"Anime #{dup_code}"),
            "original_title": None,
            "year": None,
            "media_type": "anime",
            "url": f"https://t.me/ANITOOBUZ_BOT?start={dup_code}",
            "poster_url": raw.get("image"),
            "status": "already_exists",
            "reason": f"Birlashtirilgan dublikat kartochka (Asosiy kod: #{parent_code})",
            "attempts": 0,
            "tmdb_id": None,
            "priority": 0,
            "payload": {"duplicate_of": parent_code},
        })

    print(f"Mapped {len(DUPLICATE_CARDS)} duplicate cards to already_exists.")

    # 3. Process Standalone anime
    for it in raw_items:
        c = str(it.get("id"))
        if c in handled_codes:
            continue
        handled_codes.add(c)
        nom = it.get("nom", "").strip()
        if not nom:
            continue

        known = KNOWN_STANDALONE.get(c, {})
        title = known.get("title") or nom
        tmdb_id = known.get("tmdb_id")
        media_type = known.get("media_type", "anime")
        year_val = None
        try:
            if it.get("yili") and str(it.get("yili")).isdigit():
                y = int(it.get("yili"))
                if 1950 <= y <= 2030:
                    year_val = y
        except:
            pass
        ep_count = None
        try:
            if it.get("qismi") and str(it.get("qismi")).isdigit():
                ep_count = int(it.get("qismi"))
        except:
            pass

        payload = {
            "episodes_count": ep_count,
            "verified": bool(tmdb_id),
        }
        records_to_sync.append({
            "source": "anitoob",
            "source_id": c,
            "title": title,
            "original_title": nom,
            "year": year_val,
            "media_type": media_type,
            "url": f"https://t.me/ANITOOBUZ_BOT?start={c}",
            "poster_url": it.get("image"),
            "status": "queued",
            "reason": None,
            "attempts": 0,
            "tmdb_id": tmdb_id,
            "priority": priority_counter,
            "payload": payload,
        })
        priority_counter -= 1

    print(f"Total AniToob records to sync: {len(records_to_sync)}")

    # 4. Upsert directly into PostgreSQL ingest_items table
    async with async_session_factory() as session:
        upsert_sql = """
        INSERT INTO ingest_items (
            source, source_id, title, original_title, year, media_type,
            url, poster_url, status, reason, attempts, tmdb_id, priority, payload, updated_at
        ) VALUES (
            :source, :source_id, :title, :original_title, :year, :media_type,
            :url, :poster_url, :status, :reason, :attempts, :tmdb_id, :priority, :payload, NOW()
        )
        ON CONFLICT (source, source_id) DO UPDATE SET
            title = EXCLUDED.title,
            original_title = COALESCE(EXCLUDED.original_title, ingest_items.original_title),
            year = COALESCE(EXCLUDED.year, ingest_items.year),
            media_type = EXCLUDED.media_type,
            url = EXCLUDED.url,
            poster_url = COALESCE(EXCLUDED.poster_url, ingest_items.poster_url),
            status = CASE 
                WHEN ingest_items.status = 'published' THEN 'published'
                WHEN EXCLUDED.status = 'already_exists' THEN 'already_exists'
                ELSE 'queued'
            END,
            reason = EXCLUDED.reason,
            attempts = CASE WHEN ingest_items.status = 'published' THEN ingest_items.attempts ELSE 0 END,
            tmdb_id = COALESCE(EXCLUDED.tmdb_id, ingest_items.tmdb_id),
            priority = EXCLUDED.priority,
            payload = ingest_items.payload || EXCLUDED.payload,
            updated_at = NOW();
        """
        import json as _json
        batch_params = []
        for r in records_to_sync:
            batch_params.append({
                "source": r["source"],
                "source_id": r["source_id"],
                "title": r["title"],
                "original_title": r["original_title"],
                "year": r["year"],
                "media_type": r["media_type"],
                "url": r["url"],
                "poster_url": r["poster_url"],
                "status": r["status"],
                "reason": r["reason"],
                "attempts": r["attempts"],
                "tmdb_id": r["tmdb_id"],
                "priority": r["priority"],
                "payload": _json.dumps(r["payload"]),
            })

        await session.execute(text(upsert_sql), batch_params)
        await session.commit()
        print(f"Successfully synced {len(batch_params)} AniToob records into PostgreSQL!")

if __name__ == "__main__":
    asyncio.run(sync())
