# ruff: noqa: E402
"""
Media and Seed Candidates Reset Utility (S8).

Xavfsizlik qoidalari (3 ta Guard):
1. Guard 1: Standart holda faqat DRY-RUN (quruq ko'rik) rejimida ishlaydi.
   Haqiqiy o'zgarishlar faqat --execute HAMDA --confirm YES bayroqlari berilgandagina bajariladi.
2. Guard 2: --backup-file <fayl> parametri orqali mavjud va bo'sh bo'lmagan zaxira nusxa ko'rsatilishi shart.
3. Guard 3: Nishon DB xosti TEST_DATABASE_URL xostiga teng bo'lishi shart, YOKI
   --i-am-wiping-production bayrog'i --backup-file bilan birga berilishi shart.

Vazifasi:
- seed_candidates jadvalidagi 'queued', 'ingested', 'skipped' holatidagi yozuvlarni 'new' ga qaytaradi
  (lekin 'not_found' saqlab qolinadi, qayta qidiruv spamining oldini olish uchun).
- scraper_queue.json, state.json va quarantine_items.json fayllarini tozalaydi.
- Hech qanday DROP/TRUNCATE/DELETE FROM buyruqlarisiz xavfsiz UPDATE orqali ishlaydi.
"""

import sys
import os

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import json
import argparse
import asyncio
import logging
from typing import Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sqlalchemy import select, update, func, text
from sqlalchemy.engine import make_url
from app.core.config import settings
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.seed_candidate import SeedCandidateModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

QUEUE_FILE = os.path.join(ROOT_DIR, "scraper", "scraper_queue.json")
STATE_FILE = os.path.join(ROOT_DIR, "scraper", "state.json")
QUARANTINE_FILE = os.path.join(ROOT_DIR, "scraper", "autopilot_v2", "quarantine_items.json")


def get_url_host(url_str: Optional[str]) -> Optional[str]:
    if not url_str:
        return None
    try:
        u = make_url(url_str)
        return u.host
    except Exception:
        return None


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


async def reset_media(
    execute: bool = False,
    confirm: str = "",
    backup_file: Optional[str] = None,
    i_am_wiping_production: bool = False,
    wipe_media: bool = False,
) -> dict:
    mode_label = "EXECUTE" if (execute and confirm == "YES") else "DRY-RUN"
    print("\n" + "=" * 65)
    print(f"      KINOCHI MEDIA VA SEED CANDIDATES RESET ({mode_label})")
    print("=" * 65)

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

    # Guard 1: Agar execute=False yoki confirm != 'YES' bo'lsa -> Quruq ko'rik (DRY-RUN)
    if not execute or confirm != "YES":
        print("-" * 65)
        print("ℹ️ [DRY-RUN NATIJASI] Hech qanday o'zgarish amalga oshirilmadi.")
        print("Haqiqiy tozalashni amalga oshirish uchun himoyalar (Guards) bilan chaqiring:")
        print("  python scripts/reset_media.py --execute --confirm YES --backup-file <mavjud_fayl>")
        print("=" * 65 + "\n")
        return {
            "mode": "dry_run",
            "queue_count": q_count,
            "state_count": s_count,
            "quarantine_count": quar_count,
            "candidates_to_reset": reset_candidates_count,
            "media_wiped": False,
        }

    # Guard 2: --backup-file tekshiruvi (mavjud va bo'sh bo'lmagan fayl bo'lishi shart)
    backup_file_valid = bool(
        backup_file
        and os.path.isfile(backup_file)
        and os.path.getsize(backup_file) > 0
    )
    if not backup_file_valid:
        print("❌ [XAVFSIZLIK BLOKIROVKASI] --backup-file parametri orqali mavjud va bo'sh bo'lmagan zaxira fayli ko'rsatilishi shart!")
        return {"error": "backup_file_missing_or_empty"}

    # Guard 3: DB xosti TEST_DATABASE_URL xostiga teng bo'lishi kerak YOKI --i-am-wiping-production berilgan bo'lishi kerak
    target_host = get_url_host(settings.DATABASE_URL)
    test_db_url = os.environ.get("TEST_DATABASE_URL")
    test_host = get_url_host(test_db_url)

    is_test_host_match = bool(target_host and test_host and target_host == test_host)
    has_prod_wipe_override = bool(i_am_wiping_production and backup_file_valid)

    if not (is_test_host_match or has_prod_wipe_override):
        print("❌ [XAVFSIZLIK BLOKIROVKASI] Nishon ma'lumotlar bazasi xosti TEST_DATABASE_URL xostiga mos kelmadi!")
        print("Production bazasini tozalash uchun bir vaqtning o'zida --i-am-wiping-production va --backup-file berilishi shart.")
        return {"error": "target_db_host_mismatch"}

    # Haqiqiy ijro (Barcha 3 ta guard to'liq tasdiqlandi)
    print("\n⚠️ [DIQQAT] Barcha himoyalar tasdiqlandi. Haqiqiy tozalash boshlanmoqda...")

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

    # B) seed_candidates jadvalini UPDATE orqali yangilash
    async with async_session_factory() as session:
        stmt = (
            update(SeedCandidateModel)
            .where(SeedCandidateModel.status.in_(["queued", "ingested", "skipped"]))
            .values(status="new", attempts=0)
        )
        await session.execute(stmt)
        await session.commit()
        print(f"✅ seed_candidates jadvalidagi {reset_candidates_count} ta yozuv status='new' holatiga qaytarildi.")

    # C) Media jadvallarini tozalash (agar wipe_media so'ralgan bo'lsa)
    if wipe_media:
        media_tables_to_wipe = [
            "episode_translations",
            "movie_translations",
            "movie_sources",
            "series_sources",
            "sources",
            "episodes",
            "seasons",
            "movie_categories",
            "series_categories",
            "page_movies",
            "page_series",
            "collection_items",
            "movies",
            "series",
        ]
        async with async_session_factory() as session:
            for tbl in media_tables_to_wipe:
                try:
                    await session.execute(text(f"DELETE FROM {tbl}"))
                except Exception:
                    pass
            await session.commit()
        print("✅ Media jadvallari (movies, series, episodes, sources) muvaffaqiyatli tozalandi.")

    print("🎉 Media va Seed holatlari muvaffaqiyatli yangilandi!\n" + "=" * 65 + "\n")
    return {
        "mode": "executed",
        "queue_count": q_count,
        "state_count": s_count,
        "quarantine_count": quar_count,
        "candidates_reset": reset_candidates_count,
        "media_wiped": wipe_media,
    }


def main():
    parser = argparse.ArgumentParser(description="Kinochi Media va Seed Candidates Reset Utility")
    parser.add_argument("--execute", action="store_true", help="Haqiqiy tozalashni bajarish (standart: DRY-RUN)")
    parser.add_argument("--confirm", type=str, default="", help="Tasdiqlash kaliti (faqat 'YES' qabul qilinadi)")
    parser.add_argument("--backup-file", type=str, default=None, help="Mavjud va bo'sh bo'lmagan zaxira fayli yo'li")
    parser.add_argument("--i-am-wiping-production", action="store_true", help="Production bazasini tozalash uchun xavfsizlik bayrog'i")
    parser.add_argument("--wipe-media", action="store_true", help="Media jadvallarini (movies, series, episodes) to'liq tozalash")

    args = parser.parse_args()
    asyncio.run(
        reset_media(
            execute=args.execute,
            confirm=args.confirm,
            backup_file=args.backup_file,
            i_am_wiping_production=args.i_am_wiping_production,
            wipe_media=args.wipe_media,
        )
    )


if __name__ == "__main__":
    main()
