"""
Resume downloading missing episodes for incomplete anime:
1. Ishdan bo'shatilgan qora askarning hayoti (kawaii_ajdfoowe)
2. Berserk (kawaii_aghvavlf)
3. Zindondan baxt izlash xatomi? V (kawaii_aafwhqqq)
"""

import os
import sys
import asyncio
import logging

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, "bot", ".env"))
if os.path.join(BASE_DIR, "backend") not in sys.path:
    sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("ResumeAnime")

from scraper.queue_manager import QueueManager
from scraper.duplicate_checker import DuplicateChecker
from scraper.telethon_moderator_pipeline import TelethonModeratorPipeline, create_telethon_client

TARGET_IDS = [
    "kawaii_aghvavlf",  # Berserk (13 eps)
    "kawaii_aafwhqqq",  # Zindondan baxt izlash xatomi? V (15 eps)
]

async def main():
    print("=" * 60)
    print("🚀 CHALA QOLGAN ANIMELARNI OXIRIGACHA YUKLASH BOSHLANMOQDA")
    print("=" * 60)

    qm = QueueManager()
    checker = DuplicateChecker()
    await checker.refresh_cache(force=True)

    client = create_telethon_client()
    await client.connect()
    if not await client.is_user_authorized():
        print("❌ Telegram client avtorizatsiyadan o'tmagan!")
        return

    pipeline = TelethonModeratorPipeline(client=client, duplicate_checker=checker)

    try:
        for idx, target_id in enumerate(TARGET_IDS, 1):
            item = qm.items.get(target_id)
            if not item:
                print(f"⚠️ {target_id} navbatda topilmadi, o'tkazib yuborildi.")
                continue

            print(f"\n[{idx}/{len(TARGET_IDS)}] 🎬 '{item.title}' ({target_id}) davom ettirilmoqda...")
            try:
                success = await pipeline.run_kawaii_anime(item=item)
                if success:
                    print(f"✅ '{item.title}' barcha qismlari muvaffaqiyatli yakunlandi!")
                    qm.update_status(item.id, "completed")
                else:
                    print(f"⚠️ '{item.title}' to'liq yakunlanmadi.")
            except Exception as e:
                logger.exception(f"❌ '{item.title}' yuklashda xatolik: {e}")

            if idx < len(TARGET_IDS):
                print("⏳ Keyingi anime oldidan 4 soniya tanaffus...")
                await asyncio.sleep(4.0)

    finally:
        await client.disconnect()
        print("\n🏁 Barcha animelarni yuklash jarayoni yakunlandi!")

if __name__ == "__main__":
    asyncio.run(main())
