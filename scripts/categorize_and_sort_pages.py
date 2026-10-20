import asyncio
import os
import sys
import logging
from sqlalchemy import text
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(".")
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))

from app.infrastructure.db.session import async_session_factory
from app.core.cache import delete_cache_pattern

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("categorize_all")

# 1. Barcha Multfilm (G'arb animatsiyalari) kino ID lari
MULTFILM_MOVIE_IDS = {
    # Shrek
    847, 848, 849, 850, 880,
    # Kung Fu Panda
    851, 852, 853, 854,
    # Muzlik davri (Ice Age)
    855, 856, 857, 858, 859, 881,
    # Madagaskar
    860, 861, 862,
    # O'rgimchak odam animatsiyalari (Spider-Verse)
    863, 864,
    # O'yinchoqlar tarixi (Toy Story)
    876, 877, 878, 879,
    # Qirol Sher va Mufasa
    949, 950, 951, 952, 953,
    # Yangi multfilmlar
    977,  # Vall-i (WALL-E)
    978,  # Up — Tepaga
    979,  # Kokoning siri (Coco)
    980,  # Ratatuy (Ratatouille)
    991,  # Bolakay, ko‘rsichqon, tulki va ot
    999,  # Mortal Kombat: Chayonning qasosi
    # Betxoven (barcha qismlari multfilm sahifasiga)
    940, 941, 942, 943,
}

# 2. Barcha Anime kinolari (Anime movies)
ANIME_MOVIE_IDS = {
    986,   # Ovoz shakli (A Silent Voice)
    987,   # Sening isming (Your Name.)
    988,   # Yonar qo'ng'izlar qabristoni (Grave of the Fireflies)
    989,   # Ruhlar olami (Spirited Away)
    990,   # Sening oshqozon osti bezingni yemoqchiman (I Want to Eat Your Pancreas)
    992,   # KIKI: Yetkazib berish xizmati (Kiki's Delivery Service)
    993,   # Nafis so‘zlar bog‘i (The Garden of Words)
    994,   # Suzume (Suzume)
    995,   # Josee: yo‘lbars va baliq (Josee, the Tiger and the Fish)
    996,   # Yozgi tunnel, xayrlashuv eshigi (The Tunnel to Summer)
    997,   # Aura: Koga Maryuinning so‘nggi jangi
    998,   # Shamol ko‘tarilmoqda (The Wind Rises)
    1000,  # Seni doim sevganman (I've Always Liked You)
    1001,  # Arra odam: Reze hikoyasi (Chainsaw Man – Reze Arc)
    1002,  # Jodugarlar jangi 0 (Jujutsu Kaisen 0)
}

# 3. Barcha Anime seriallari (Anime series)
ANIME_SERIES_IDS = {
    1024,  # Jodugarlar jangi (Jujutsu Kaisen)
    1025,  # Titanlar hujumi (Attack on Titan)
}

# 4. Barcha Dorama seriallari (Korean dramas)
DORAMA_SERIES_IDS = {
    1002,  # Kalmar o'yini (Squid Game)
    1008,  # Barchamiz o'likmiz (All of Us Are Dead)
}

async def sort_and_categorize(apply: bool = False):
    logger.info("=== BARCHA ANIME, MULTFILM VA DORAMALARNI O'Z SAHIFALARIGA SARALASH ===")
    logger.info(f"Rejim: {'APPLY' if apply else 'DRY-RUN'}")

    async with async_session_factory() as session:
        # Sahifalarni olish
        pages_res = await session.execute(text("SELECT id, title, slug FROM pages ORDER BY id"))
        pages = {r[2].lower(): (r[0], r[1]) for r in pages_res.fetchall()}
        
        anime_page_id = pages.get("anime")[0] if "anime" in pages else 1
        dorama_page_id = pages.get("dorama")[0] if "dorama" in pages else 5
        cartoon_page_id = pages.get("cartoon")[0] if "cartoon" in pages else 8

        logger.info(f"Sahifalar: Anime=ID {anime_page_id}, Dorama=ID {dorama_page_id}, Multfilm=ID {cartoon_page_id}")

        # Kategoriyalarni olish
        anime_cat = (await session.execute(text("SELECT id FROM categories WHERE name ILIKE 'anime' OR slug ILIKE 'anime'"))).first()
        anime_cat_id = anime_cat[0] if anime_cat else 2

        anim_cat = (await session.execute(text("SELECT id FROM categories WHERE name ILIKE '%animatsiya%' OR slug ILIKE '%animation%'"))).first()
        anim_cat_id = anim_cat[0] if anim_cat else 22

        drama_cat = (await session.execute(text("SELECT id FROM categories WHERE name ILIKE 'drama'"))).first()
        drama_cat_id = drama_cat[0] if drama_cat else 3

        # 1. ANIME KINOLARNI BIRIKTIRISH
        logger.info(f"\n--- ANIME KINOLAR ({len(ANIME_MOVIE_IDS)} ta) ---")
        for mid in sorted(ANIME_MOVIE_IDS):
            m_title = (await session.execute(text("SELECT title FROM movies WHERE id = :id"), {"id": mid})).scalar()
            logger.info(f"  [Anime Kino] [{mid}] '{m_title}' -> Page {anime_page_id} ('Anime')")
            if apply:
                await session.execute(text("INSERT INTO page_movie (page_id, movie_id) VALUES (:pid, :mid) ON CONFLICT DO NOTHING"), {"pid": anime_page_id, "mid": mid})
                await session.execute(text("INSERT INTO movie_category (movie_id, category_id) VALUES (:mid, :cid) ON CONFLICT DO NOTHING"), {"mid": mid, "cid": anime_cat_id})

        # 2. ANIME SERIALLARNI BIRIKTIRISH
        logger.info(f"\n--- ANIME SERIALLAR ({len(ANIME_SERIES_IDS)} ta) ---")
        for sid in sorted(ANIME_SERIES_IDS):
            s_title = (await session.execute(text("SELECT title FROM series WHERE id = :id"), {"id": sid})).scalar()
            logger.info(f"  [Anime Serial] [{sid}] '{s_title}' -> Page {anime_page_id} ('Anime')")
            if apply:
                await session.execute(text("INSERT INTO page_series (page_id, series_id) VALUES (:pid, :sid) ON CONFLICT DO NOTHING"), {"pid": anime_page_id, "sid": sid})
                await session.execute(text("INSERT INTO series_category (series_id, category_id) VALUES (:sid, :cid) ON CONFLICT DO NOTHING"), {"sid": sid, "cid": anime_cat_id})

        # 3. MULTFILMLARNI BIRIKTIRISH
        logger.info(f"\n--- MULTFILMLAR ({len(MULTFILM_MOVIE_IDS)} ta) ---")
        for mid in sorted(MULTFILM_MOVIE_IDS):
            m_title = (await session.execute(text("SELECT title FROM movies WHERE id = :id"), {"id": mid})).scalar()
            logger.info(f"  [Multfilm] [{mid}] '{m_title}' -> Page {cartoon_page_id} ('Multfilm')")
            if apply:
                await session.execute(text("INSERT INTO page_movie (page_id, movie_id) VALUES (:pid, :mid) ON CONFLICT DO NOTHING"), {"pid": cartoon_page_id, "mid": mid})
                await session.execute(text("INSERT INTO movie_category (movie_id, category_id) VALUES (:mid, :cid) ON CONFLICT DO NOTHING"), {"mid": mid, "cid": anim_cat_id})

        # 4. DORAMALARNI BIRIKTIRISH
        logger.info(f"\n--- DORAMALAR ({len(DORAMA_SERIES_IDS)} ta) ---")
        for sid in sorted(DORAMA_SERIES_IDS):
            s_title = (await session.execute(text("SELECT title FROM series WHERE id = :id"), {"id": sid})).scalar()
            logger.info(f"  [Dorama] [{sid}] '{s_title}' -> Page {dorama_page_id} ('Doramalar')")
            if apply:
                await session.execute(text("INSERT INTO page_series (page_id, series_id) VALUES (:pid, :sid) ON CONFLICT DO NOTHING"), {"pid": dorama_page_id, "sid": sid})
                await session.execute(text("INSERT INTO series_category (series_id, category_id) VALUES (:sid, :cid) ON CONFLICT DO NOTHING"), {"sid": sid, "cid": drama_cat_id})

        if apply:
            await session.commit()
            logger.info("\nBarcha ma'lumotlar bazada muvaffaqiyatli saqlandi!")

            # Keshlarni tozalash
            try:
                await delete_cache_pattern("*")
                logger.info("Keshlar muvaffaqiyatli tozalandi!")
            except Exception as e:
                logger.warning(f"Kesh tozalashda ogohlantirish: {e}")

            # Yakuniy statistika
            anime_m_cnt = (await session.execute(text("SELECT count(*) FROM page_movie WHERE page_id = :pid"), {"pid": anime_page_id})).scalar()
            anime_s_cnt = (await session.execute(text("SELECT count(*) FROM page_series WHERE page_id = :pid"), {"pid": anime_page_id})).scalar()
            cartoon_m_cnt = (await session.execute(text("SELECT count(*) FROM page_movie WHERE page_id = :pid"), {"pid": cartoon_page_id})).scalar()
            dorama_s_cnt = (await session.execute(text("SELECT count(*) FROM page_series WHERE page_id = :pid"), {"pid": dorama_page_id})).scalar()

            kinolar_cnt = (await session.execute(text("""
                SELECT count(*) FROM movies m
                WHERE NOT EXISTS (SELECT 1 FROM page_movie pm WHERE pm.movie_id = m.id)
                  AND NOT EXISTS (SELECT 1 FROM movie_category mc WHERE mc.movie_id = m.id AND mc.category_id = 2)
            """))).scalar()

            seriallar_cnt = (await session.execute(text("""
                SELECT count(*) FROM series s
                WHERE NOT EXISTS (SELECT 1 FROM page_series ps WHERE ps.series_id = s.id)
                  AND NOT EXISTS (SELECT 1 FROM series_category sc WHERE sc.series_id = s.id AND sc.category_id = 2)
            """))).scalar()

            logger.info("==================================================")
            logger.info("               YAKUNIY TAQSIMOT                   ")
            logger.info("==================================================")
            logger.info(f"1. Anime sahifasi ('/p/anime'): {anime_m_cnt} ta kino + {anime_s_cnt} ta serial = {anime_m_cnt + anime_s_cnt} ta media")
            logger.info(f"2. Multfilm sahifasi ('/p/Cartoon'): {cartoon_m_cnt} ta multfilm")
            logger.info(f"3. Doramalar sahifasi ('/p/Dorama'): {dorama_s_cnt} ta dorama")
            logger.info(f"4. Kinolar sahifasi ('/movies'): {kinolar_cnt} ta sof kino (multfilm va animelarsiz!)")
            logger.info(f"5. Seriallar sahifasi ('/series'): {seriallar_cnt} ta sof serial (dorama va animelarsiz!)")
            logger.info("==================================================")

if __name__ == "__main__":
    apply_flag = "--apply" in sys.argv
    asyncio.run(sort_and_categorize(apply=apply_flag))
