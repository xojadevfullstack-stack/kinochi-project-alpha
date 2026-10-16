"""
Media and Seed Candidates Reset Utility (S8).

Xavfsizlik qoidalari (3 ta Guard):
1. Guard 1: Standart holda faqat DRY-RUN (quruq ko'rik) rejimida ishlaydi.
2. Guard 2: O'zgarishlar faqat --execute HAMDA --confirm YES bayroqlari berilgandagina bajariladi.
3. Guard 3: Production muhitida (APP_ENV=production) tasodifiy ishga tushishdan bloklangan.

Vazifasi:
- seed_candidates jadvalidagi 'queued', 'ingested', 'skipped' holatidagi yozuvlarni 'new' ga qaytaradi
  (lekin 'not_found' saqlab qolinadi, qayta qidiruv spamining oldini olish uchun).
- scraper_queue.json, state.json va quarantine_items.json fayllarini tozalaydi.
- Hech qanday DROP/TRUNCATE/DELETE FROM buyruqlarisiz xavfsiz UPDATE orqali ishlaydi.
"""

import sys
import os
import json
import argparse
import asyncio
import logging

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sqlalchemy import select, update, func, text
from app.core.config import settings
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.seed_candidate import SeedCandidateModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

QUEUE_FILE = os.path.join(ROOT_DIR, "scraper", "scraper_queue.json")
STATE_FILE = os.path.join(ROOT_DIR, "scraper", "state.json")
QUARANTINE_FILE = os.path.join(ROOT_DIR, "scraper", "autopilot_v2", "quarantine_items.json")


def inspect_file_items(filepath: str) -> int:
    if not os.path.exists(filepath):
        return 0
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return len(data)
            elif isinstance(data, dict):
                return len(data)
    except Exception:
        pass
    return 0


async def reset_media(execute: bool = False, confirm: str = "") -> dict:
    mode_label = "EXECUTE" if (execute and confirm == "YES") else "DRY-RUN"
    print("\n" + "=" * 65)
    print(f"      KINOCHI MEDIA VA SEED CANDIDATES RESET ({mode_label})")
    print("=" * 65)

    # Guard 3: Production himoyasi
    if settings.APP_ENV == "production" and execute:
        print("❌ [XAVFSIZLIK BLOKIROVKASI] Production muhitida ushbu skriptni ishga tushirish qat'iyan taqiqlanadi!")
        return {"error": "production_blocked"}

    # 1. Fayllardagi elementlarni tekshirish
    q_count = inspect_file_items(QUEUE_FILE)
    s_count = inspect_file_items(STATE_FILE)
    quar_count = inspect_file_items(QUARANTINE_FILE)

    print(f"📄 Navbat fayli (scraper_queue.json)         : {q_count} ta element")
    print(f"📄 Parser holati (state.json)               : {s_count} ta manba holati")
    print(f"📄 Karantin qutisi (quarantine_items.json)   : {quar_count} ta element")

    # 2. seed_candidates jadvalini tekshirish
    async with async_session_factory() as session:
        count_q = await session.execute(
            select(func.count(SeedCandidateModel.id)).where(
                SeedCandidateModel.status.in_(["queued", "ingested", "skipped"])
            )
        )
        reset_candidates_count = count_q.scalar() or 0
        print(f"🗄️ Qayta 'new' holatiga o'tadigan seedlar : {reset_candidates_count} ta ('queued'/'ingested'/'skipped')")

    if not execute or confirm != "YES":
        print("-" * 65)
        print("ℹ️ [DRY-RUN NATIJASI] Hech qanday o'zgarish amalga oshirilmadi.")
        print("Haqiqiy tozalashni amalga oshirish uchun 3 ta himoya (Guards) bilan chaqiring:")
        print("  python scripts/reset_media.py --execute --confirm YES")
        print("=" * 65 + "\n")
        return {
            "mode": "dry_run",
            "queue_count": q_count,
            "state_count": s_count,
            "quarantine_count": quar_count,
            "candidates_to_reset": reset_candidates_count,
        }

    # Haqiqiy ijro (Faqat execute=True va confirm='YES' bo'lganda)
    print("\n⚠️ [DIQQAT] 3 ta himoya tasdiqlandi. Haqiqiy tozalash boshlanmoqda...")

    # A) JSON fayllarni xavfsiz tozalash
    try:
        with open(QUEUE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        print("✅ scraper_queue.json bo'shatildi ([])")
    except Exception as e:
        logger.error(f"scraper_queue.json ni tozalashda xatolik: {e}")

    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)
        print("✅ state.json boshlang'ich holatga keltirildi ({})")
    except Exception as e:
        logger.error(f"state.json ni tozalashda xatolik: {e}")

    try:
        with open(QUARANTINE_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, ensure_ascii=False, indent=2)
        print("✅ quarantine_items.json bo'shatildi ([])")
    except Exception as e:
        logger.error(f"quarantine_items.json ni tozalashda xatolik: {e}")

    # B) seed_candidates jadvalini UPDATE orqali yangilash (No DELETE / No TRUNCATE)
    async with async_session_factory() as session:
        stmt = (
            update(SeedCandidateModel)
            .where(SeedCandidateModel.status.in_(["queued", "ingested", "skipped"]))
            .values(status="new", attempts=0)
        )
        await session.execute(stmt)
        await session.commit()
        print(f"✅ seed_candidates jadvalidagi {reset_candidates_count} ta yozuv status='new' holatiga qaytarildi.")

    print("🎉 Media va Seed holatlari muvaffaqiyatli yangilandi!\n" + "=" * 65 + "\n")
    return {
        "mode": "executed",
        "queue_count": q_count,
        "state_count": s_count,
        "quarantine_count": quar_count,
        "candidates_reset": reset_candidates_count,
    }


def main():
    parser = argparse.ArgumentParser(description="Kinochi Media va Seed Candidates Reset Utility")
    parser.add_argument("--execute", action="store_true", help="Haqiqiy tozalashni bajarish (standart: DRY-RUN)")
    parser.add_argument("--confirm", type=str, default="", help="Tasdiqlash kaliti (faqat 'YES' qabul qilinadi)")

    args = parser.parse_args()
    asyncio.run(reset_media(execute=args.execute, confirm=args.confirm))


if __name__ == "__main__":
    main()
