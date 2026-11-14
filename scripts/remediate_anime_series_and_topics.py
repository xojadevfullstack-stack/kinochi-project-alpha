import asyncio
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
sys.path.insert(0, BASE_DIR)

from app.core.config import settings
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.cache import delete_cache_pattern

async def main():
    engine = create_async_engine(settings.DATABASE_URL)
    async with engine.begin() as conn:
        print("=== 1. REMEDIATING SERIES #1092 (Obs 86 Show -> 86: Eighty Six) ===")
        await conn.execute(text("""
            UPDATE series
            SET title = '86: Eighty Six',
                tmdb_id = 100565,
                release_year = 2021,
                imdb_rating = 8.1,
                tmdb_rating = 8.1,
                poster_url = 'https://image.tmdb.org/t/p/w500/1RAD6bMQayJPoO8ry4vJy3GwCYt.jpg',
                description = 'San-Magnoliya Respublikasi uzoq vaqtdan beri Giadian imperiyasining "Legion" deb nomlangan uchuvchisiz dronlari qamalida edi. Hukumat urush qurbonlarsiz olib borilmoqda deb da''vo qiladi, ammo shahar devorlaridan tashqarida 86-sektor yoshlari shafqatsiz janglarda jon bermoqda.'
            WHERE id = 1092
        """))
        print("  Updated Series #1092")

        print("\n=== 2. REMEDIATING SERIES #1052 (Naruto The Ocean Cut -> Naruto: Shippuden, Season 2) ===")
        await conn.execute(text("""
            UPDATE series
            SET title = 'Naruto: Shippuden',
                tmdb_id = 31910,
                release_year = 2007,
                imdb_rating = 8.5,
                tmdb_rating = 8.5,
                poster_url = 'https://image.tmdb.org/t/p/w500/kV27j3Nz4d5z8u6mN3EJw9RiLg2.jpg',
                description = 'Naruto olamida ikki yil ko''z ochib yumguncha o''tib ketdi. Qahramonlar o''z mahoratlarini oshirish uchun mashhur Sanninlar qo''lida tayyorgarlik ko''rdilar. Naruto o''zining yangi jangovar kuchiga tayanib, yangi xavf-xatarlarga qarshi kurashadi.'
            WHERE id = 1052
        """))
        # Update season number from 1 to 2
        await conn.execute(text("""
            UPDATE seasons
            SET season_number = 2,
                title = '2-fasl'
            WHERE series_id = 1052
        """))
        # Update display_code in episodes: replace S1- with S2-
        await conn.execute(text("""
            UPDATE episodes
            SET display_code = REPLACE(display_code, 'S1-', 'S2-')
            WHERE season_id IN (SELECT id FROM seasons WHERE series_id = 1052)
        """))
        print("  Updated Series #1052 and Season to 2")

        print("\n=== 3. REMEDIATING SERIES #1095 (Shu'lat oxiri haremasi -> Dunyo oxiridagi haram) ===")
        await conn.execute(text("""
            UPDATE series
            SET title = 'Dunyo oxiridagi haram (World''s End Harem)',
                tmdb_id = 103409,
                release_year = 2022,
                imdb_rating = 7.5,
                tmdb_rating = 7.5,
                poster_url = 'https://image.tmdb.org/t/p/w500/h3OE30FudEPEhNMpbmcHt0ELD6s.jpg',
                description = 'Dahshatli virus sayyoradagi deyarli barcha erkak zotini qirib yubordi. Tirik qolganlar anabioz holatiga tushirilgan. Besh yillik uyqudan so''ng, Reito mutlaqo o''zgargan dunyoga ko''z ochadi va insoniyatni qayta tiklash mas''uliyatini his qiladi.'
            WHERE id = 1095
        """))
        print("  Updated Series #1095")

        print("\n=== 4. REMEDIATING SERIES #1063 (Hujumkor titanlar: So'nggi hujum -> Titanlar hujumi) ===")
        await conn.execute(text("""
            UPDATE series
            SET title = 'Titanlar hujumi (Attack on Titan)',
                tmdb_id = 1429,
                release_year = 2013,
                imdb_rating = 8.7,
                tmdb_rating = 8.7,
                poster_url = 'https://image.tmdb.org/t/p/w500/hTP1DtLGFamjfu8WqjnuQdP1n4i.jpg',
                description = 'Insoniyat ulkan devorlar ortida odamxo''r titanlardan himoyalanib yashamoqda. Bir kuni ulkan titan devorni buzib kiradi va Eren Yeger onasining o''limidan so''ng barcha titanlarni qirib tashlashga qasam ichadi.'
            WHERE id = 1063
        """))
        print("  Updated Series #1063")

        print("\n=== 5. CLEANING UP ORPHAN SOURCE #1213 (Topic 7035) ===")
        await conn.execute(text("DELETE FROM series_sources WHERE id = 1213"))
        print("  Deleted Source #1213 from DB")

    await engine.dispose()

    try:
        await delete_cache_pattern("cache:series:*")
        await delete_cache_pattern("cache:episode:*")
        print("  Flushed Redis series/episode cache")
    except Exception as e:
        print(f"  Redis cache flush note: {e}")

    # Now delete topic 7035 in Telegram
    try:
        from scraper.telethon_moderator_pipeline import TelethonModeratorPipeline, create_telethon_client, AUTO_TOPIC_CHAT_ID
        from scraper.duplicate_checker import DuplicateChecker
        print(f"\n=== 6. DELETING TOPIC #7035 FROM TELEGRAM (Chat: {AUTO_TOPIC_CHAT_ID}) ===")
        client = create_telethon_client()
        await client.connect()
        try:
            pipeline = TelethonModeratorPipeline(client=client, duplicate_checker=DuplicateChecker())
            deleted = await pipeline._delete_topic_safe(AUTO_TOPIC_CHAT_ID, 7035)
            print(f"  Topic #7035 Telegram delete status: {deleted}")
        finally:
            await client.disconnect()
    except Exception as e:
        print(f"  Telegram topic delete error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
