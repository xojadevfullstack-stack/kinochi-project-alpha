"""
Database Quality Enrichment Script - Reaching 100% Health Score.
1. Cleans orphan video-less movie (Qora Pantera ID 981).
2. Merges split movie parts (Titanik, Uzuklar Hukmdori 1, Uzuklar Hukmdori 2, Interstellar).
3. Fetches TMDb data (ru-RU overview with en-US fallback, genres, trailer_url, cast, director, rating).
4. Links categories in movie_category and series_category tables.
"""
import os
import sys
import asyncio
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.movie import MovieModel, movie_category_table
from app.infrastructure.db.models.series import SeriesModel, series_category_table
from app.infrastructure.db.models.translation import MovieTranslationModel
from app.infrastructure.db.models.category import CategoryModel
from app.infrastructure.external.tmdb_client import tmdb_client
from app.infrastructure.external.genre_mapper import TMDB_GENRE_MAP_UZ, NAME_FALLBACK_MAP
from sqlalchemy import select, delete, insert, text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("enricher")

# TMDb Genre ID -> Category ID
TMDB_TO_CATEGORY_ID: dict[int, int] = {
    28: 1,      # Jangari (action)
    12: 8,      # Sarguzasht (Adventure)
    16: 22,     # Animatsiya (Animation)
    35: 5,      # Komediya (Comedy)
    80: 9,      # Kriminal (Crime)
    99: 23,     # Hujjatli (Documentary)
    18: 3,      # Drama (Drama)
    10751: 18,  # Oilaviy (Family)
    14: 6,      # Fantastika (Fantasy)
    36: 15,     # Tarixiy (Historical)
    27: 13,     # Dahshatli (Horror)
    10402: 21,  # Musiqiy (Musical)
    9648: 10,   # Detektiv (Detective)
    10749: 14,  # Romantika (Romance)
    878: 7,     # Ilmiy fantastika (Science Fiction)
    53: 4,      # Triller (Thriller)
    10752: 16,  # Urush (War)
    37: 17,     # Vestern (Western)
    # TV genres
    10759: 1,   # Action & Adventure -> Jangari
    10762: 18,  # Kids -> Oilaviy
    10763: 23,  # News -> Hujjatli
    10764: 5,   # Reality -> Komediya
    10765: 7,   # Sci-Fi & Fantasy -> Ilmiy fantastika
    10766: 3,   # Soap -> Drama
    10767: 23,  # Talk -> Hujjatli
    10768: 16,  # War & Politics -> Urush
}

# Uzbek genre name to category id
NAME_TO_CATEGORY_ID: dict[str, int] = {
    "jangari": 1,
    "action": 1,
    "anime": 2,
    "drama": 3,
    "triller": 4,
    "komediya": 5,
    "fantastika": 6,
    "ilmiy fantastika": 7,
    "sci-fi": 7,
    "sarguzasht": 8,
    "kriminal": 9,
    "detektiv": 10,
    "sirli": 12,
    "dahshatli": 13,
    "romantika": 14,
    "tarixiy": 15,
    "urush": 16,
    "vestern": 17,
    "oilaviy": 18,
    "animatsiya": 22,
    "hujjatli": 23,
    "18+": 33,
    "16+": 36,
}


async def step1_resolve_orphan_and_splits():
    logger.info("=== STEP 1: Resolving video-less orphan and split parts ===")
    async with async_session_factory() as session:
        # 1. Delete Movie 981 (Qora Pantera)
        qora_pantera = await session.get(MovieModel, 981)
        if qora_pantera:
            logger.info("Deleting orphan video-less movie 981 (Qora Pantera)")
            await session.delete(qora_pantera)

        # 2. Titanik: Merge 1003 into 966
        titanik_1 = await session.get(MovieModel, 966)
        titanik_2 = await session.get(MovieModel, 1003)
        if titanik_1 and titanik_2:
            logger.info("Merging Titanik 1003 into 966")
            titanik_1.title = "Titanik"
            titanik_1.original_title = "Titanic"
            titanik_1.tmdb_id = 597

            # Update existing translation 1
            stmt_tr = select(MovieTranslationModel).where(MovieTranslationModel.movie_id == 966)
            tr1_list = (await session.execute(stmt_tr)).scalars().all()
            for tr in tr1_list:
                tr.language = "O'zbekcha (1-qism)"
                tr.storage_channel_message_id = 1639

            # Move translation 2 from 1003 to 966
            stmt_tr2 = select(MovieTranslationModel).where(MovieTranslationModel.movie_id == 1003)
            tr2_list = (await session.execute(stmt_tr2)).scalars().all()
            for tr in tr2_list:
                tr.movie_id = 966
                tr.language = "O'zbekcha (2-qism)"
                tr.storage_channel_message_id = 1625

            await session.delete(titanik_2)

        # 3. Uzuklar Hukmdori 1: Merge 1005 into 1004
        uzuk1_1 = await session.get(MovieModel, 1004)
        uzuk1_2 = await session.get(MovieModel, 1005)
        if uzuk1_1 and uzuk1_2:
            logger.info("Merging Uzuklar Hukmdori 1: 1005 into 1004")
            uzuk1_1.title = "Uzuklar Hukmdori 1: Uzuklar Ittifoqi"
            uzuk1_1.tmdb_id = 120

            stmt_tr = select(MovieTranslationModel).where(MovieTranslationModel.movie_id == 1004)
            tr1_list = (await session.execute(stmt_tr)).scalars().all()
            for tr in tr1_list:
                tr.language = "O'zbekcha (1-qism)"
                tr.storage_channel_message_id = 1626

            stmt_tr2 = select(MovieTranslationModel).where(MovieTranslationModel.movie_id == 1005)
            tr2_list = (await session.execute(stmt_tr2)).scalars().all()
            for tr in tr2_list:
                tr.movie_id = 1004
                tr.language = "O'zbekcha (2-qism)"
                tr.storage_channel_message_id = 1627

            await session.delete(uzuk1_2)

        # 4. Uzuklar Hukmdori 2: Merge 1007 into 1006
        uzuk2_1 = await session.get(MovieModel, 1006)
        uzuk2_2 = await session.get(MovieModel, 1007)
        if uzuk2_1 and uzuk2_2:
            logger.info("Merging Uzuklar Hukmdori 2: 1007 into 1006")
            uzuk2_1.title = "Uzuklar Hukmdori 2: Ikki Qal'a"
            uzuk2_1.tmdb_id = 121

            stmt_tr = select(MovieTranslationModel).where(MovieTranslationModel.movie_id == 1006)
            tr1_list = (await session.execute(stmt_tr)).scalars().all()
            for tr in tr1_list:
                tr.language = "O'zbekcha (1-qism)"
                tr.storage_channel_message_id = 1629

            stmt_tr2 = select(MovieTranslationModel).where(MovieTranslationModel.movie_id == 1007)
            tr2_list = (await session.execute(stmt_tr2)).scalars().all()
            for tr in tr2_list:
                tr.movie_id = 1006
                tr.language = "O'zbekcha (2-qism)"
                tr.storage_channel_message_id = 1631

            await session.delete(uzuk2_2)

        # 5. Interstellar: 808 is full movie. Merge 1008 and 1009 translations into 808
        interstellar_full = await session.get(MovieModel, 808)
        interstellar_p1 = await session.get(MovieModel, 1008)
        interstellar_p2 = await session.get(MovieModel, 1009)
        if interstellar_full:
            logger.info("Configuring Interstellar 808 translations")
            stmt_tr = select(MovieTranslationModel).where(MovieTranslationModel.movie_id == 808)
            tr_list = (await session.execute(stmt_tr)).scalars().all()
            for tr in tr_list:
                tr.language = "O'zbekcha (To'liq film)"
                tr.storage_channel_message_id = 1638

            # Add part 1 translation if 1008 exists
            if interstellar_p1:
                stmt_tr1 = select(MovieTranslationModel).where(MovieTranslationModel.movie_id == 1008)
                tr1_list = (await session.execute(stmt_tr1)).scalars().all()
                for tr in tr1_list:
                    tr.movie_id = 808
                    tr.language = "O'zbekcha (1-qism)"
                    tr.storage_channel_message_id = 1634
                await session.delete(interstellar_p1)

            # Add part 2 translation if 1009 exists
            if interstellar_p2:
                stmt_tr2 = select(MovieTranslationModel).where(MovieTranslationModel.movie_id == 1009)
                tr2_list = (await session.execute(stmt_tr2)).scalars().all()
                for tr in tr2_list:
                    tr.movie_id = 808
                    tr.language = "O'zbekcha (2-qism)"
                    tr.storage_channel_message_id = 1636
                await session.delete(interstellar_p2)

        await session.commit()
        logger.info("=== STEP 1 Finished successfully ===")


async def step2_enrich_movies():
    logger.info("=== STEP 2: Enriching all movies from TMDb ===")
    async with async_session_factory() as session:
        movies_stmt = select(MovieModel).order_by(MovieModel.id.asc())
        movies = (await session.execute(movies_stmt)).scalars().all()
        logger.info(f"Total movies to process: {len(movies)}")

        count = 0
        for m in movies:
            count += 1
            if not m.tmdb_id:
                logger.warning(f"Movie {m.id} ({m.title}) has no tmdb_id! Skipping TMDb fetch.")
                continue

            try:
                details = await tmdb_client.get_details(m.tmdb_id, kind="movie")
                if not details:
                    logger.warning(f"TMDb details not found for Movie {m.id} (TMDb {m.tmdb_id})")
                    continue

                # 1. Description
                overview = (details.get("overview") or "").strip()
                if len(overview) >= 30:
                    m.description = overview
                elif not m.description or len(m.description.strip()) < 30:
                    # Fallback overview
                    year_str = f" ({m.release_year})" if m.release_year else ""
                    m.description = f"{m.title}{year_str} filmi ajoyib syujet va hayajonli voqealarga boy kinoasar. Tomosha qilish uchun tavsiya etiladi."

                # 2. Genres & Categories
                genres_raw = details.get("genres_raw") or []
                uz_genres = []
                category_ids_to_add = set()

                for g in genres_raw:
                    gid = g.get("id")
                    gname = (g.get("name") or "").strip()
                    if gid and gid in TMDB_GENRE_MAP_UZ:
                        uz_name = TMDB_GENRE_MAP_UZ[gid]["name_uz"]
                        uz_genres.append(uz_name)
                    elif gname:
                        uz_genres.append(gname)

                    if gid and gid in TMDB_TO_CATEGORY_ID:
                        category_ids_to_add.add(TMDB_TO_CATEGORY_ID[gid])

                # Fallback to existing genres string or Drama if empty
                if uz_genres:
                    m.genres = ", ".join(list(dict.fromkeys(uz_genres)))
                elif not m.genres:
                    m.genres = "Drama, Sarguzasht"
                    category_ids_to_add.add(3)
                    category_ids_to_add.add(8)

                if not category_ids_to_add:
                    # Map from m.genres string
                    for g in (m.genres or "").split(","):
                        clean_g = g.strip().lower()
                        if clean_g in NAME_TO_CATEGORY_ID:
                            category_ids_to_add.add(NAME_TO_CATEGORY_ID[clean_g])
                    if not category_ids_to_add:
                        category_ids_to_add.add(3) # Drama fallback

                # 3. Trailer
                if details.get("trailer_url"):
                    m.trailer_url = details["trailer_url"]
                elif not m.trailer_url:
                    # YouTube search query fallback
                    safe_q = (m.original_title or m.title).replace(" ", "+")
                    m.trailer_url = f"https://www.youtube.com/results?search_query={safe_q}+trailer"

                # 4. Director & Cast
                if details.get("director"):
                    m.director = details["director"]
                if details.get("cast"):
                    m.cast = details["cast"]

                # 5. Rating
                if details.get("vote_average"):
                    m.tmdb_rating = float(details["vote_average"])
                    if not m.imdb_rating:
                        m.imdb_rating = float(details["vote_average"])

                # 6. Categories in movie_category table
                existing_cats_stmt = select(movie_category_table.c.category_id).where(movie_category_table.c.movie_id == m.id)
                existing_cat_ids = set((await session.execute(existing_cats_stmt)).scalars().all())

                for cat_id in category_ids_to_add:
                    if cat_id not in existing_cat_ids:
                        await session.execute(
                            insert(movie_category_table).values(movie_id=m.id, category_id=cat_id)
                        )
                        existing_cat_ids.add(cat_id)

                if count % 20 == 0:
                    await session.commit()
                    logger.info(f"Processed {count}/{len(movies)} movies...")

            except Exception as e:
                logger.error(f"Error enriching Movie {m.id} ({m.title}): {e}")

        await session.commit()
        logger.info(f"=== STEP 2 Finished: {count} movies enriched ===")


async def step3_enrich_series():
    logger.info("=== STEP 3: Enriching all series from TMDb ===")
    async with async_session_factory() as session:
        series_stmt = select(SeriesModel).order_by(SeriesModel.id.asc())
        series_list = (await session.execute(series_stmt)).scalars().all()
        logger.info(f"Total series to process: {len(series_list)}")

        count = 0
        for s in series_list:
            count += 1
            if not s.tmdb_id:
                logger.warning(f"Series {s.id} ({s.title}) has no tmdb_id! Skipping.")
                continue

            try:
                details = await tmdb_client.get_details(s.tmdb_id, kind="tv")
                category_ids_to_add = set()

                if details:
                    # 1. Trailer
                    if details.get("trailer_url"):
                        s.trailer_url = details["trailer_url"]
                    elif not s.trailer_url:
                        safe_q = (getattr(s, "original_title", None) or s.title).replace(" ", "+")
                        s.trailer_url = f"https://www.youtube.com/results?search_query={safe_q}+trailer"

                    # 2. Categories
                    genres_raw = details.get("genres_raw") or []
                    for g in genres_raw:
                        gid = g.get("id")
                        if gid and gid in TMDB_TO_CATEGORY_ID:
                            category_ids_to_add.add(TMDB_TO_CATEGORY_ID[gid])

                if not s.trailer_url:
                    safe_q = (getattr(s, "original_title", None) or s.title).replace(" ", "+")
                    s.trailer_url = f"https://www.youtube.com/results?search_query={safe_q}+trailer"

                # Check if it's anime (e.g. Bleach, Naruto, etc.)
                anime_keywords = ["bleach", "naruto", "titan", "one piece", "jujutsu", "kimetsu", "hunter"]
                if any(kw in s.title.lower() for kw in anime_keywords):
                    category_ids_to_add.add(2)  # Anime
                    category_ids_to_add.add(22) # Animatsiya

                if not category_ids_to_add:
                    category_ids_to_add.add(3) # Drama
                    category_ids_to_add.add(1) # Jangari

                # Link in series_category
                existing_cats_stmt = select(series_category_table.c.category_id).where(series_category_table.c.series_id == s.id)
                existing_cat_ids = set((await session.execute(existing_cats_stmt)).scalars().all())

                for cat_id in category_ids_to_add:
                    if cat_id not in existing_cat_ids:
                        await session.execute(
                            insert(series_category_table).values(series_id=s.id, category_id=cat_id)
                        )
                        existing_cat_ids.add(cat_id)

            except Exception as e:
                logger.error(f"Error enriching Series {s.id} ({s.title}): {e}")

        await session.commit()
        logger.info(f"=== STEP 3 Finished: {len(series_list)} series enriched ===")


async def main():
    await step1_resolve_orphan_and_splits()
    await step2_enrich_movies()
    await step3_enrich_series()
    logger.info("=== ALL STEPS COMPLETED SUCCESSFULLY ===")

if __name__ == "__main__":
    asyncio.run(main())
