import sys, os, asyncio, re, logging
BASE_DIR = os.path.abspath(".")
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.external.tmdb_client import tmdb_client
from app.infrastructure.external.translator import translator_service
from app.core.cache import delete_cache_pattern
from scraper.smart_enricher import clean_synopsis_text, is_telegram_caption_junk
from sqlalchemy import text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("fix_anime_db")

# Known specific anime fixes
SPECIAL_SERIES = {
    515: {
        "title": "Sehr yaratuvchisi qanday qilib boshqa dunyoda",
        "tmdb_id": 258912,
        "content_type": "tv",
        "poster_url": "https://image.tmdb.org/t/p/w500/wKe1FmUAcSukpfEn5s6747pBwLD.jpg",
        "imdb_rating": 7.5
    },
    516: {
        "title": "Avatar ang haqidagi afsona",
        "tmdb_id": 246,
        "content_type": "tv",
        "poster_url": "https://image.tmdb.org/t/p/w500/yaGt4GIutpbXHsv48tWceWg6s56.jpg",
        "imdb_rating": 8.8
    },
    517: {
        "title": "Qip-qizil Ragna",
        "tmdb_id": 195459,
        "content_type": "tv",
        "poster_url": "https://image.tmdb.org/t/p/w500/z3ymAW3LveYyq0TqHSicuU8S5tG.jpg",
        "imdb_rating": 7.3
    },
    518: {
        "title": "Re:Zero hayotni noldan boshlash",
        "tmdb_id": 65942,
        "content_type": "tv",
        "poster_url": "https://image.tmdb.org/t/p/w500/oHqYrPAsIiTD5m4DuxumV4er8BU.jpg",
        "imdb_rating": 8.1
    },
    519: {
        "title": "Men G'ayritabiiy Holat muvaffaqiyatsiz mahorati bilan eng kuchli bo'lib, hamma narsani yo'q qilaman",
        "tmdb_id": 245285,
        "content_type": "tv",
        "poster_url": "https://image.tmdb.org/t/p/w500/vsbcM6ImjctW0bLaj1SStaTmVT5.jpg",
        "imdb_rating": 7.4
    }
}

SPECIAL_MOVIES = {
    621: {
        "title": "Salom dunyo",
        "tmdb_id": 604605,
        "content_type": "movie",
        "poster_url": "https://image.tmdb.org/t/p/w500/vmizP4G4EWsxNf6PLOvGNaFJ89Y.jpg",
        "imdb_rating": 7.3,
        "tmdb_rating": 7.3
    }
}

async def fix_all():
    logger.info("🚀 Anime ma'lumotlarini tozalash va to'g'irlash skripti boshlandi...")

    async with async_session_factory() as session:
        # 1. SPECIAL SERIES FIXES (515, 516, 517, 518, 519)
        for s_id, s_data in SPECIAL_SERIES.items():
            logger.info(f"👉 Maxsus serial to'g'irlanmoqda: ID {s_id} - {s_data['title']}")
            det = await tmdb_client.get_details(s_data["tmdb_id"], content_type=s_data["content_type"])
            overview_uz = None
            if det and det.get("overview"):
                trans_desc, _ = await translator_service.translate_to_uzbek(det["overview"])
                if trans_desc:
                    overview_uz = clean_synopsis_text(trans_desc, s_data["title"], "series")
            
            poster = s_data["poster_url"] or (det.get("poster_url") if det else None)
            rating = s_data["imdb_rating"] or (round(det["vote_average"], 1) if det and det.get("vote_average") else None)

            # Update DB
            if overview_uz:
                await session.execute(text("""
                    UPDATE series
                    SET tmdb_id = :tmdb_id,
                        poster_url = :poster_url,
                        imdb_rating = :imdb_rating,
                        description = :description
                    WHERE id = :id
                """), {
                    "tmdb_id": s_data["tmdb_id"],
                    "poster_url": poster,
                    "imdb_rating": rating,
                    "description": overview_uz,
                    "id": s_id
                })
            else:
                await session.execute(text("""
                    UPDATE series
                    SET tmdb_id = :tmdb_id,
                        poster_url = :poster_url,
                        imdb_rating = :imdb_rating
                    WHERE id = :id
                """), {
                    "tmdb_id": s_data["tmdb_id"],
                    "poster_url": poster,
                    "imdb_rating": rating,
                    "id": s_id
                })

            # Link to page 1 (Anime) and category 2
            await session.execute(text("""
                INSERT INTO page_series (page_id, series_id) VALUES (1, :s_id)
                ON CONFLICT DO NOTHING
            """), {"s_id": s_id})
            await session.execute(text("""
                INSERT INTO series_category (series_id, category_id) VALUES (:s_id, 2)
                ON CONFLICT DO NOTHING
            """), {"s_id": s_id})
            logger.info(f"  ✅ Serial {s_id} yangilandi! Poster: {poster}, Rating: {rating}")

        # 2. SPECIAL MOVIES FIXES (621)
        for m_id, m_data in SPECIAL_MOVIES.items():
            logger.info(f"👉 Maxsus kino to'g'irlanmoqda: ID {m_id} - {m_data['title']}")
            det = await tmdb_client.get_details(m_data["tmdb_id"], content_type=m_data["content_type"])
            overview_uz = None
            if det and det.get("overview"):
                trans_desc, _ = await translator_service.translate_to_uzbek(det["overview"])
                if trans_desc:
                    overview_uz = clean_synopsis_text(trans_desc, m_data["title"], "movie")
            
            poster = m_data["poster_url"] or (det.get("poster_url") if det else None)
            rating = m_data["imdb_rating"]

            if overview_uz:
                await session.execute(text("""
                    UPDATE movies
                    SET tmdb_id = :tmdb_id,
                        poster_url = :poster_url,
                        imdb_rating = :imdb_rating,
                        tmdb_rating = :tmdb_rating,
                        description = :description
                    WHERE id = :id
                """), {
                    "tmdb_id": m_data["tmdb_id"],
                    "poster_url": poster,
                    "imdb_rating": rating,
                    "tmdb_rating": m_data["tmdb_rating"],
                    "description": overview_uz,
                    "id": m_id
                })
            else:
                await session.execute(text("""
                    UPDATE movies
                    SET tmdb_id = :tmdb_id,
                        poster_url = :poster_url,
                        imdb_rating = :imdb_rating,
                        tmdb_rating = :tmdb_rating
                    WHERE id = :id
                """), {
                    "tmdb_id": m_data["tmdb_id"],
                    "poster_url": poster,
                    "imdb_rating": rating,
                    "tmdb_rating": m_data["tmdb_rating"],
                    "id": m_id
                })

            await session.execute(text("""
                INSERT INTO page_movie (page_id, movie_id) VALUES (1, :m_id)
                ON CONFLICT DO NOTHING
            """), {"m_id": m_id})
            await session.execute(text("""
                INSERT INTO movie_category (movie_id, category_id) VALUES (:m_id, 2)
                ON CONFLICT DO NOTHING
            """), {"m_id": m_id})
            logger.info(f"  ✅ Kino {m_id} yangilandi! Poster: {poster}, Rating: {rating}")

        # 3. FIX ALL ANIME MOVIES: Ensure page_id=1, fix ratings & telegram descriptions
        res_m = await session.execute(text("""
            SELECT m.id, m.title, m.tmdb_id, m.imdb_rating, m.tmdb_rating, m.description, m.poster_url
            FROM movies m
            JOIN movie_category mc ON m.id = mc.movie_id
            WHERE mc.category_id = 2 OR m.title ILIKE '%anime%'
        """))
        anime_movies = res_m.fetchall()
        logger.info(f"🔎 Bazada {len(anime_movies)} ta anime kino topildi. Tekshirilmoqda...")

        for row in anime_movies:
            m_id, m_title, m_tmdb, m_imdb, m_tmdb_rat, m_desc, m_poster = row
            
            # Ensure page_id = 1
            await session.execute(text("""
                INSERT INTO page_movie (page_id, movie_id) VALUES (1, :m_id)
                ON CONFLICT DO NOTHING
            """), {"m_id": m_id})

            updated_fields = {}

            # Check TMDb details if rating or description or poster missing/broken
            needs_desc = is_telegram_caption_junk(m_desc) or (m_desc and m_desc.startswith("🍿"))
            needs_rating = m_imdb is None or m_imdb == 0.0 or m_tmdb_rat is None

            if m_tmdb and (needs_desc or needs_rating or not m_poster):
                try:
                    det = await tmdb_client.get_details(m_tmdb, content_type="movie")
                    if det:
                        if not m_poster and det.get("poster_url"):
                            updated_fields["poster_url"] = det["poster_url"]
                        
                        vote_avg = round(det["vote_average"], 1) if det.get("vote_average") else None
                        if needs_rating and vote_avg:
                            updated_fields["imdb_rating"] = det.get("imdb_rating") or vote_avg
                            updated_fields["tmdb_rating"] = vote_avg
                        
                        if needs_desc and det.get("overview"):
                            trans_desc, _ = await translator_service.translate_to_uzbek(det["overview"])
                            if trans_desc:
                                clean_t = clean_synopsis_text(trans_desc, m_title, "movie")
                                if clean_t and not clean_t.startswith("🍿"):
                                    updated_fields["description"] = clean_t
                except Exception as e:
                    logger.warning(f"Error checking TMDb for movie {m_id}: {e}")

            # If movie 618 (Arra odam arc), search for Chainsaw Man
            if m_id == 618:
                try:
                    det = await tmdb_client.get_details(114410, content_type="tv")
                    if det:
                        updated_fields["tmdb_id"] = 114410
                        if det.get("poster_url"):
                            updated_fields["poster_url"] = det["poster_url"]
                        vote_avg = round(det["vote_average"], 1) if det.get("vote_average") else 8.5
                        updated_fields["imdb_rating"] = vote_avg
                        updated_fields["tmdb_rating"] = vote_avg
                        if det.get("overview"):
                            trans_desc, _ = await translator_service.translate_to_uzbek(det["overview"])
                            if trans_desc:
                                updated_fields["description"] = clean_synopsis_text(trans_desc, m_title, "movie")
                except Exception as e:
                    logger.warning(f"Error fixing movie 618: {e}")

            # Apply updates if any
            if updated_fields:
                set_clauses = [f"{k} = :{k}" for k in updated_fields.keys()]
                params = {**updated_fields, "id": m_id}
                await session.execute(text(f"""
                    UPDATE movies SET {', '.join(set_clauses)} WHERE id = :id
                """), params)
                logger.info(f"  🎬 Kino {m_id} ({m_title}) yangilandi: {list(updated_fields.keys())}")

        # 4. FIX ALL ANIME SERIES: Ensure page_id=1, fix ratings & telegram descriptions
        res_s = await session.execute(text("""
            SELECT s.id, s.title, s.tmdb_id, s.imdb_rating, s.description, s.poster_url
            FROM series s
            JOIN series_category sc ON s.id = sc.series_id
            WHERE sc.category_id = 2 OR s.title ILIKE '%anime%'
        """))
        anime_series = res_s.fetchall()
        logger.info(f"🔎 Bazada {len(anime_series)} ta anime serial topildi. Tekshirilmoqda...")

        for row in anime_series:
            s_id, s_title, s_tmdb, s_imdb, s_desc, s_poster = row

            # Ensure page_id = 1
            await session.execute(text("""
                INSERT INTO page_series (page_id, series_id) VALUES (1, :s_id)
                ON CONFLICT DO NOTHING
            """), {"s_id": s_id})

            updated_fields = {}
            needs_desc = is_telegram_caption_junk(s_desc) or (s_desc and s_desc.startswith("🍿"))
            needs_rating = s_imdb is None or s_imdb == 0.0

            if m_tmdb := s_tmdb:
                if needs_rating or needs_desc or not s_poster:
                    try:
                        det = await tmdb_client.get_details(m_tmdb, content_type="tv")
                        if det:
                            if not s_poster and det.get("poster_url"):
                                updated_fields["poster_url"] = det["poster_url"]
                            
                            vote_avg = round(det["vote_average"], 1) if det.get("vote_average") else None
                            if needs_rating and vote_avg:
                                updated_fields["imdb_rating"] = det.get("imdb_rating") or vote_avg
                            
                            if needs_desc and det.get("overview"):
                                trans_desc, _ = await translator_service.translate_to_uzbek(det["overview"])
                                if trans_desc:
                                    clean_t = clean_synopsis_text(trans_desc, s_title, "series")
                                    if clean_t and not clean_t.startswith("🍿"):
                                        updated_fields["description"] = clean_t
                    except Exception as e:
                        logger.warning(f"Error checking TMDb for series {s_id}: {e}")

            if updated_fields:
                set_clauses = [f"{k} = :{k}" for k in updated_fields.keys()]
                params = {**updated_fields, "id": s_id}
                await session.execute(text(f"""
                    UPDATE series SET {', '.join(set_clauses)} WHERE id = :id
                """), params)
                logger.info(f"  📺 Serial {s_id} ({s_title}) yangilandi: {list(updated_fields.keys())}")

        await session.commit()
        logger.info("🎉 Barcha o'zgarishlar PostgreSQL bazasiga muvaffaqiyatli saqlandi!")

    # 5. Clear Redis caches
    try:
        await delete_cache_pattern("cache:movies:*")
        await delete_cache_pattern("cache:series:*")
        logger.info("🧹 Redis kesh tozalab tashlandi!")
    except Exception as e:
        logger.warning(f"Redis kesh tozalashda ogohlantirish: {e}")

    logger.info("✅ BARCHA VAZIFALAR MUVAFFAQIYATLI YAKUNLANDI!")

if __name__ == "__main__":
    asyncio.run(fix_all())
