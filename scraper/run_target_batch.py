import asyncio
import sys
import os
import logging

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend")))

from scraper.telethon_moderator_pipeline import create_telethon_client, TelethonModeratorPipeline
from scraper.duplicate_checker import DuplicateChecker
from scraper.queue_manager import QueueItem
from app.core.cache import delete_cache_pattern

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MOVIES_AND_SPECIALS = [
    # 5-kino: Avatar (2009)
    {
        "id": "asilmedia_avatar_2009",
        "title": "Avatar",
        "original_title": "Avatar",
        "year": 2009,
        "media_type": "movie",
        "category": "5-Kino (Avatar)"
    },
    # 1-multfilm: Shrek 2
    {
        "id": "asilmedia_shrek_2_2004",
        "title": "Shrek 2",
        "original_title": "Shrek 2",
        "year": 2004,
        "media_type": "multfilm",
        "category": "1-Multfilm (Shrek 2)"
    },
    # 1-anime: Titanlar hujumi
    {
        "id": "asilmedia_titanlar_hujumi_2024",
        "title": "Titanlar hujumi",
        "original_title": "Attack on Titan",
        "year": 2024,
        "media_type": "anime",
        "category": "1-Anime (Titanlar hujumi)"
    },
]

async def run():
    client = create_telethon_client()
    await client.connect()
    
    checker = DuplicateChecker()
    await checker.refresh_cache(force=True)
    pipeline = TelethonModeratorPipeline(client=client, duplicate_checker=checker)

    # 1. Kinolar, multfilm va anime
    for entry in MOVIES_AND_SPECIALS:
        print("\n" + "=" * 65)
        print(f"🚀 YUKLASH: [{entry['category']}] {entry['title']} ({entry['year']})")
        print("=" * 65)
        
        item = QueueItem(
            id=entry["id"],
            source="asilmedia",
            title=entry["title"],
            original_title=entry["original_title"],
            year=entry["year"],
            media_type=entry.get("media_type", "movie"),
            url="https://asilmedia.org"
        )
        try:
            res = await pipeline.run_single_movie(item=item, target_bot="asilmediabot")
            print(f"✅ Natija [{entry['title']}]: {'MUVAFFAQIYATLI' if res else 'XATOLIK'}")
        except Exception as e:
            print(f"❌ Xatolik [{entry['title']}]: {e}")
        
        await asyncio.sleep(4.0)

    # 2. Dorama (Kalmar o'yini - 1-fasl)
    print("\n" + "=" * 65)
    print(f"🚀 YUKLASH: [1-Dorama] Kalmar O'yini (2021)")
    print("=" * 65)
    dorama_item = QueueItem(
        id="asilmedia_kalmar_oyini_2021",
        source="asilmedia",
        title="Kalmar O'yini",
        original_title="Squid Game",
        year=2021,
        media_type="dorama",
        url="https://asilmedia.org"
    )
    try:
        res = await pipeline.run_single_series(item=dorama_item, target_bot="asilmediabot")
        print(f"✅ Natija [Kalmar O'yini]: {'MUVAFFAQIYATLI' if res else 'XATOLIK'}")
    except Exception as e:
        print(f"❌ Xatolik [Kalmar O'yini]: {e}")

    await asyncio.sleep(4.0)

    # 3. Serial (Chernobil 2019)
    print("\n" + "=" * 65)
    print(f"🚀 YUKLASH: [1-Serial] Chernobil (2019)")
    print("=" * 65)
    series_item = QueueItem(
        id="asilmedia_chernobil_2019",
        source="asilmedia",
        title="Chernobil",
        original_title="Chernobyl",
        year=2019,
        media_type="series",
        url="https://asilmedia.org"
    )
    try:
        res = await pipeline.run_single_series(item=series_item, target_bot="asilmediabot")
        print(f"✅ Natija [Chernobil]: {'MUVAFFAQIYATLI' if res else 'XATOLIK'}")
    except Exception as e:
        print(f"❌ Xatolik [Chernobil]: {e}")

    try:
        await delete_cache_pattern("cache:*")
    except Exception:
        pass

    print("\n" + "=" * 65)
    print("🎉 BARCHA YUKLASHLAR TUGADI!")
    print("=" * 65)
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(run())
