import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import asyncio
import os
import random
import uuid
import html
import io
import logging
import httpx
from telethon import TelegramClient
from telethon.sessions import StringSession
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.core.config import settings
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.translation import MovieTranslationModel
from sqlalchemy import select

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logger = logging.getLogger("franchise_migration")

TARGET_SUPERGROUP = int(settings.AUTO_TOPIC_CHAT_ID)  # -1003847632555
TARGET_STORAGE = int(settings.STORAGE_CHANNEL_ID)    # -1003762157591
OLD_STORAGE = -1003926001543

async def create_or_get_topic(client: TelegramClient, title: str) -> int:
    from telethon.tl.functions.messages import CreateForumTopicRequest
    peer = await client.get_input_entity(TARGET_SUPERGROUP)
    r_id = random.randint(1, 2**31 - 1)
    res = await client(CreateForumTopicRequest(
        peer=peer,
        title=title[:128],
        random_id=r_id
    ))
    topic_id = None
    for u in getattr(res, 'updates', []):
        if hasattr(u, 'message') and hasattr(u.message, 'id'):
            topic_id = u.message.id
            break
        elif hasattr(u, 'id'):
            topic_id = u.id
            break
    if not topic_id:
        for u in getattr(res, 'updates', []):
            if hasattr(u, 'channel_id'):
                topic_id = getattr(u, 'id', None)
    return topic_id

async def fetch_poster_bytes(url: str) -> bytes | None:
    try:
        async with httpx.AsyncClient(timeout=15) as hclient:
            res = await hclient.get(url)
            if res.status_code == 200:
                return res.content
    except Exception as e:
        logger.warning(f"Poster yuklab olishda xatolik ({url}): {e}")
    return None

async def migrate_franchise(client: TelegramClient, franchise: dict):
    fname = franchise["name"]
    logger.info(f"==================================================")
    logger.info(f"BOSHLANMOQDA: Franshiza '{fname}'")
    logger.info(f"==================================================")

    # 1. Fetch Banner Poster
    poster_bytes = await fetch_poster_bytes(franchise.get("banner_poster", ""))

    # 2. Create Topic in Supergroup
    topic_id = await create_or_get_topic(client, fname)
    logger.info(f"Topic ochildi: '{fname}' (ID: {topic_id})")
    await asyncio.sleep(1.5)

    # 3. Post Banner to Topic & Pin
    banner_caption = (
        f"🎬 <b>{html.escape(fname)}</b>\n"
        f"🎭 <b>Janr:</b> {franchise.get('genres', 'Kino to\'plam')}\n"
        f"⭐ <b>Reyting:</b> {franchise.get('rating', 'Yuqori')}\n"
        f"🇺🇿 <b>Tili:</b> O'zbek tilida (Barcha qismlar)\n\n"
        f"📖 <b>Tavsif:</b>\n{html.escape(franchise.get('description', ''))[:700]}\n\n"
        f"🍿 @kinochi_mvp_bot orqali yuklandi."
    )

    topic_banner_msg = None
    if poster_bytes:
        f_sg = io.BytesIO(poster_bytes)
        f_sg.name = "franchise_banner.jpg"
        topic_banner_msg = await client.send_file(
            TARGET_SUPERGROUP,
            file=f_sg,
            caption=banner_caption,
            reply_to=topic_id,
            parse_mode="html"
        )
    else:
        topic_banner_msg = await client.send_message(
            TARGET_SUPERGROUP,
            message=banner_caption,
            reply_to=topic_id,
            parse_mode="html"
        )

    await asyncio.sleep(1.2)

    if topic_banner_msg:
        try:
            from telethon.tl.functions.messages import UpdatePinnedMessageRequest
            await client(UpdatePinnedMessageRequest(
                peer=TARGET_SUPERGROUP,
                id=topic_banner_msg.id,
                silent=True
            ))
            logger.info(f"Franshiza banneri qadaldi (Msg ID: {topic_banner_msg.id})")
        except Exception as e:
            logger.warning(f"Bannerni qadashda ogohlantirish: {e}")

    await asyncio.sleep(1.5)

    # 4. Migrate Each Movie
    movies_list = franchise["movies"]
    for m_idx, m_info in enumerate(movies_list, start=1):
        m_title = m_info["title"]
        m_orig = m_info.get("original_title", m_title)
        m_tmdb = m_info.get("tmdb_id")
        m_poster = m_info.get("poster_url")
        m_year = m_info.get("release_year")
        m_imdb = m_info.get("imdb_rating")
        old_msg_id = m_info["old_msg_id"]

        logger.info(f"  [{m_idx}/{len(movies_list)}] Film ko'chirilmoqda: '{m_title}' ({m_year})...")

        # Fetch old video msg
        old_msg = await client.get_messages(OLD_STORAGE, ids=old_msg_id)
        if not old_msg or not (old_msg.video or old_msg.document):
            logger.warning(f"    Msg ID {old_msg_id} da video topilmadi!")
            continue

        # Check or Create Movie in DB
        async with async_session_factory() as session:
            # Check by tmdb_id or title
            movie_obj = None
            if m_tmdb:
                res = await session.execute(select(MovieModel).where(MovieModel.tmdb_id == m_tmdb))
                movie_obj = res.scalar_one_or_none()
            if not movie_obj:
                res = await session.execute(select(MovieModel).where(MovieModel.title == m_title))
                movie_obj = res.scalar_one_or_none()

            m_code = movie_obj.code if movie_obj else uuid.uuid4().hex[:8]

            caption_movie = (
                f"🎬 <b>{html.escape(m_title)}</b> ({m_year})\n"
                f"🔑 <b>Film kodi:</b> <code>{m_code}</code>\n"
                f"⭐ <b>IMDb:</b> {m_imdb}/10\n"
                f"🇺🇿 <b>Tili:</b> O'zbek tilida\n\n"
                f"🍿 @kinochi_mvp_bot orqali yuklandi."
            )

            # Send to Storage Channel
            new_st_msg = await client.send_file(
                TARGET_STORAGE,
                file=old_msg.media,
                caption=caption_movie,
                parse_mode="html"
            )
            await asyncio.sleep(1.0)

            # Send to Supergroup Topic
            await client.send_file(
                TARGET_SUPERGROUP,
                file=old_msg.media,
                caption=caption_movie,
                reply_to=topic_id,
                parse_mode="html"
            )
            await asyncio.sleep(1.2)

            # Update or Insert Movie in DB
            if movie_obj:
                movie_obj.source_chat_id = TARGET_SUPERGROUP
                movie_obj.source_topic_id = topic_id
                movie_obj.source_type = "superguruh"
                movie_obj.custom_source_name = "Kinochi @kinochi_mvp_bot"
                if m_poster:
                    movie_obj.poster_url = m_poster
                if m_tmdb:
                    movie_obj.tmdb_id = m_tmdb
                if m_imdb:
                    movie_obj.imdb_rating = m_imdb
                if m_year:
                    movie_obj.release_year = m_year
            else:
                movie_obj = MovieModel(
                    title=m_title,
                    original_title=m_orig,
                    code=m_code,
                    release_year=m_year,
                    imdb_rating=m_imdb,
                    tmdb_id=m_tmdb,
                    poster_url=m_poster,
                    publish_status="published",
                    source_chat_id=TARGET_SUPERGROUP,
                    source_topic_id=topic_id,
                    source_type="superguruh",
                    custom_source_name="Kinochi @kinochi_mvp_bot"
                )
                session.add(movie_obj)

            await session.flush()

            # Translation record
            res_trans = await session.execute(select(MovieTranslationModel).where(MovieTranslationModel.movie_id == movie_obj.id))
            trans_obj = res_trans.scalar_one_or_none()
            if trans_obj:
                trans_obj.storage_channel_message_id = new_st_msg.id
            else:
                trans_obj = MovieTranslationModel(
                    movie_id=movie_obj.id,
                    language="O'zbekcha",
                    storage_channel_message_id=new_st_msg.id
                )
                session.add(trans_obj)

            await session.commit()
            logger.info(f"    [OK] Film '{m_title}' muvaffaqiyatli saqlandi! (Kod: {m_code})")

    logger.info(f"=== Franshiza '{fname}' barcha qismlari muvaffaqiyatli ko'chirildi! ===\n")

ALL_FRANCHISES = [
    # 1. QASOSKORLAR
    {
        "name": "Qasoskorlar (Avengers Saga)",
        "banner_poster": "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg",
        "description": "Marvel Kinokoinotining eng ulkan superqahramonlar jamoasi — Qasoskorlar barcha filmlari to'liq to'plami.",
        "genres": "Fantastika, Jangari, Sarguzasht",
        "rating": "8.5/10",
        "movies": [
            {"title": "Qasoskorlar 1", "original_title": "The Avengers", "tmdb_id": 24428, "poster_url": "https://image.tmdb.org/t/p/w500/RYMX2wcKCBAr24UyPD7xwmjaTn.jpg", "release_year": 2012, "imdb_rating": 8.0, "old_msg_id": 2755},
            {"title": "Qasoskorlar 2: Altron davri", "original_title": "Avengers: Age of Ultron", "tmdb_id": 99861, "poster_url": "https://image.tmdb.org/t/p/w500/4ssDuvEDkS9urvtLgi1KgdfqBZw.jpg", "release_year": 2015, "imdb_rating": 7.3, "old_msg_id": 2755},
            {"title": "Qasoskorlar 3: Cheksizlik jangi", "original_title": "Avengers: Infinity War", "tmdb_id": 299536, "poster_url": "https://image.tmdb.org/t/p/w500/7WsyChQLEftFiDOVTGkv3hFpyyt.jpg", "release_year": 2018, "imdb_rating": 8.4, "old_msg_id": 2757},
            {"title": "Qasoskorlar 4: Intiho", "original_title": "Avengers: Endgame", "tmdb_id": 299534, "poster_url": "https://image.tmdb.org/t/p/w500/or06FN3Dka5tukK1e9sl16pB3iy.jpg", "release_year": 2019, "imdb_rating": 8.4, "old_msg_id": 2759},
        ]
    },
    # 2. TEMIR ODAM
    {
        "name": "Temir odam (Iron Man)",
        "banner_poster": "https://image.tmdb.org/t/p/w500/78lPtwv72eTNqFW9COBYI0dWDJa.jpg",
        "description": "Milliarder, ixtirochi va pleyboy Toni Starkning temir zirh yaratib superqahramonga aylanishi tarixi.",
        "genres": "Fantastika, Jangari, Sarguzasht",
        "rating": "7.9/10",
        "movies": [
            {"title": "Temir odam 1", "original_title": "Iron Man", "tmdb_id": 1726, "poster_url": "https://image.tmdb.org/t/p/w500/78lPtwv72eTNqFW9COBYI0dWDJa.jpg", "release_year": 2008, "imdb_rating": 7.9, "old_msg_id": 8040},
            {"title": "Temir odam 2", "original_title": "Iron Man 2", "tmdb_id": 10138, "poster_url": "https://image.tmdb.org/t/p/w500/6WBeq40ghManXxVoNmDYbg547aN.jpg", "release_year": 2010, "imdb_rating": 7.0, "old_msg_id": 8022},
            {"title": "Temir odam 3", "original_title": "Iron Man 3", "tmdb_id": 68721, "poster_url": "https://image.tmdb.org/t/p/w500/qhPtAc1TKbMPqNvcdXSOn9Bn7hZ.jpg", "release_year": 2013, "imdb_rating": 7.1, "old_msg_id": 8018},
        ]
    },
    # 3. O'RGIMCHAK ODAM
    {
        "name": "Oʻrgimchak odam (Spider-Man)",
        "banner_poster": "https://image.tmdb.org/t/p/w500/gh4c2bhLYQEZFv375QBvjCi9G4n.jpg",
        "description": "O'rgimchak odam barcha davrlari to'plami: Tobi Maguayr, Endryu Garfild va Tom Xolland filmlari.",
        "genres": "Fantastika, Jangari, Sarguzasht",
        "rating": "8.0/10",
        "movies": [
            {"title": "O'rgimchak odam 1", "original_title": "Spider-Man", "tmdb_id": 557, "poster_url": "https://image.tmdb.org/t/p/w500/gh4c2bhLYQEZFv375QBvjCi9G4n.jpg", "release_year": 2002, "imdb_rating": 7.4, "old_msg_id": 2765},
            {"title": "O'rgimchak odam 2", "original_title": "Spider-Man 2", "tmdb_id": 558, "poster_url": "https://image.tmdb.org/t/p/w500/olxpyq9kJAZ2NU1siLshhhipq1W.jpg", "release_year": 2004, "imdb_rating": 7.5, "old_msg_id": 2769},
            {"title": "O'rgimchak odam 3", "original_title": "Spider-Man 3", "tmdb_id": 559, "poster_url": "https://image.tmdb.org/t/p/w500/2jLxvdCAxW7c2yJqqUv2g5c9j0g.jpg", "release_year": 2007, "imdb_rating": 6.3, "old_msg_id": 2767},
            {"title": "Yangi O'rgimchak odam 1", "original_title": "The Amazing Spider-Man", "tmdb_id": 1930, "poster_url": "https://image.tmdb.org/t/p/w500/fSbkk1TjVd6c7BwPZ85p9XJvNrn.jpg", "release_year": 2012, "imdb_rating": 6.9, "old_msg_id": 8030},
            {"title": "Yangi O'rgimchak odam 2: Yuksak kuchlanish", "original_title": "The Amazing Spider-Man 2", "tmdb_id": 102382, "poster_url": "https://image.tmdb.org/t/p/w500/c3OHQncTAnKFhdOTX7IgZNWTeJJ.jpg", "release_year": 2014, "imdb_rating": 6.6, "old_msg_id": 8044},
            {"title": "O'rgimchak odam: Uyga qaytish", "original_title": "Spider-Man: Homecoming", "tmdb_id": 315635, "poster_url": "https://image.tmdb.org/t/p/w500/c24sv2weTHPsmDa7jEMN0m2P3RT.jpg", "release_year": 2017, "imdb_rating": 7.4, "old_msg_id": 8026},
            {"title": "O'rgimchak odam: Uydan uzoqda", "original_title": "Spider-Man: Far From Home", "tmdb_id": 429617, "poster_url": "https://image.tmdb.org/t/p/w500/4q2NNZ4hxSATezMwPfaoVku59Kn.jpg", "release_year": 2019, "imdb_rating": 7.4, "old_msg_id": 8024},
            {"title": "O'rgimchak odam: Uyga yo'l yo'q", "original_title": "Spider-Man: No Way Home", "tmdb_id": 634649, "poster_url": "https://image.tmdb.org/t/p/w500/1g0dhYtq4irTY1GPXvft6k4YLjm.jpg", "release_year": 2021, "imdb_rating": 8.2, "old_msg_id": 2241},
        ]
    },
    # 4. BETMEN
    {
        "name": "Betmen (Batman Saga)",
        "banner_poster": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg",
        "description": "Kristofer Nolanning afsonaviy Qorong'i ritsar trilogiyasi hamda Yangi Betmen (2022) filmi to'liq to'plami.",
        "genres": "Jangari, Kriminal, Triller",
        "rating": "8.8/10",
        "movies": [
            {"title": "Betmen: Muqaddima", "original_title": "Batman Begins", "tmdb_id": 272, "poster_url": "https://image.tmdb.org/t/p/w500/1P3GslzgCFqPv29GQapNDvLOKUR.jpg", "release_year": 2005, "imdb_rating": 8.2, "old_msg_id": 2777},
            {"title": "Qorong'i ritsar", "original_title": "The Dark Knight", "tmdb_id": 155, "poster_url": "https://image.tmdb.org/t/p/w500/qJ2tW6WMUDux911r6m7haRef0WH.jpg", "release_year": 2008, "imdb_rating": 9.0, "old_msg_id": 8048},
            {"title": "Qorong'i ritsar: Afsonaning qaytishi", "original_title": "The Dark Knight Rises", "tmdb_id": 49026, "poster_url": "https://image.tmdb.org/t/p/w500/hrJ0gJ82F4r7E8c67nN1uG5aK17.jpg", "release_year": 2012, "imdb_rating": 8.4, "old_msg_id": 2775},
            {"title": "Betmen (2022)", "original_title": "The Batman", "tmdb_id": 414906, "poster_url": "https://image.tmdb.org/t/p/w500/74xTEgt7R36Fpooo50r9T25onhq.jpg", "release_year": 2022, "imdb_rating": 7.8, "old_msg_id": 2771},
        ]
    },
    # 5. KARIB DENGIZI QAROQCHILARI
    {
        "name": "Karib dengizi qaroqchilari",
        "banner_poster": "https://image.tmdb.org/t/p/w500/z8onk7LV9Mmw6zKz4hT6pzzYvlB.jpg",
        "description": "Kapitan Jek Chittak va uning g'aroyib dengiz sarguzashtlari to'liq 5 qism.",
        "genres": "Sarguzasht, Fantastika, Jangari",
        "rating": "8.0/10",
        "movies": [
            {"title": "Karib dengizi qaroqchilari 1: Qora marvarid tavqi la'nati", "original_title": "Pirates of the Caribbean: The Curse of the Black Pearl", "tmdb_id": 22, "poster_url": "https://image.tmdb.org/t/p/w500/z8onk7LV9Mmw6zKz4hT6pzzYvlB.jpg", "release_year": 2003, "imdb_rating": 8.1, "old_msg_id": 2743},
            {"title": "Karib dengizi qaroqchilari 2: Murdalar sandig'i", "original_title": "Pirates of the Caribbean: Dead Man's Chest", "tmdb_id": 58, "poster_url": "https://image.tmdb.org/t/p/w500/waFr5RVBnJg1x0c3b8r47h1qj7A.jpg", "release_year": 2006, "imdb_rating": 7.4, "old_msg_id": 2745},
            {"title": "Karib dengizi qaroqchilari 3: Dunyolar chegarasida", "original_title": "Pirates of the Caribbean: At World's End", "tmdb_id": 285, "poster_url": "https://image.tmdb.org/t/p/w500/2Y44RrqxRk1Ua9r79M3P92fNrkN.jpg", "release_year": 2007, "imdb_rating": 7.1, "old_msg_id": 2747},
            {"title": "Karib dengizi qaroqchilari 4: Noma'lum sohillarda", "original_title": "Pirates of the Caribbean: On Stranger Tides", "tmdb_id": 1865, "poster_url": "https://image.tmdb.org/t/p/w500/keGfSvTF9VRbm049ioFmNyVaPTe.jpg", "release_year": 2011, "imdb_rating": 6.6, "old_msg_id": 2749},
            {"title": "Karib dengizi qaroqchilari 5: Murdalar ertak aytmaydi", "original_title": "Pirates of the Caribbean: Dead Men Tell No Tales", "tmdb_id": 282035, "poster_url": "https://image.tmdb.org/t/p/w500/xbpSDU3p7YUGUp9msAR09huY0gO.jpg", "release_year": 2017, "imdb_rating": 6.5, "old_msg_id": 2751},
        ]
    },
    # 6. JON UIK
    {
        "name": "Jon Uik (John Wick)",
        "banner_poster": "https://image.tmdb.org/t/p/w500/fZPSMVcKrrZqJwP2200oxNIlXxO.jpg",
        "description": "Afsonaviy qotil Jon Uikning to'xtovsiz qasos jangi — barcha 4 qism to'liq to'plami.",
        "genres": "Jangari, Triller, Kriminal",
        "rating": "7.8/10",
        "movies": [
            {"title": "Jon Uik 1", "original_title": "John Wick", "tmdb_id": 245891, "poster_url": "https://image.tmdb.org/t/p/w500/fZPSMVcKrrZqJwP2200oxNIlXxO.jpg", "release_year": 2014, "imdb_rating": 7.4, "old_msg_id": 8014},
            {"title": "Jon Uik 2", "original_title": "John Wick: Chapter 2", "tmdb_id": 324552, "poster_url": "https://image.tmdb.org/t/p/w500/kL9w0D1yG4e0xVzYc2ZqfUq3F9.jpg", "release_year": 2017, "imdb_rating": 7.5, "old_msg_id": 8012},
            {"title": "Jon Uik 3: Parabellum", "original_title": "John Wick: Chapter 3 - Parabellum", "tmdb_id": 458156, "poster_url": "https://image.tmdb.org/t/p/w500/ziEuG1essDuWuC5lpWUaw1uXY2O.jpg", "release_year": 2019, "imdb_rating": 7.4, "old_msg_id": 8016},
            {"title": "Jon Uik 4", "original_title": "John Wick: Chapter 4", "tmdb_id": 603692, "poster_url": "https://image.tmdb.org/t/p/w500/vZloFAK7NKnMGKEslUsDdAFJJip.jpg", "release_year": 2023, "imdb_rating": 7.7, "old_msg_id": 2893},
        ]
    },
    # 7. XOBBIT
    {
        "name": "Xobbit (The Hobbit Trilogy)",
        "banner_poster": "https://image.tmdb.org/t/p/w500/yHA9Fc37VmpUA5oq5wji0xZY0ng.jpg",
        "description": "Bilbo Beggins, Gandalf va o'n uch pakana (gnom)larning O'rta Yer bo'ylab xavfli va aqlbovar qilmas sayohati.",
        "genres": "Fentezi, Sarguzasht",
        "rating": "7.8/10",
        "movies": [
            {"title": "Xobbit 1: Kutilmagan sayohat", "original_title": "The Hobbit: An Unexpected Journey", "tmdb_id": 49051, "poster_url": "https://image.tmdb.org/t/p/w500/yHA9Fc37VmpUA5oq5wji0xZY0ng.jpg", "release_year": 2012, "imdb_rating": 7.8, "old_msg_id": 5822},
            {"title": "Xobbit 2: Smaug xarobasi", "original_title": "The Hobbit: The Desolation of Smaug", "tmdb_id": 57158, "poster_url": "https://image.tmdb.org/t/p/w500/1q5uKjLg8B8a6WqG2Vw7H2a0s8Q.jpg", "release_year": 2013, "imdb_rating": 7.8, "old_msg_id": 5824},
            {"title": "Xobbit 3: Besh qoʻshin jangi", "original_title": "The Hobbit: The Battle of the Five Armies", "tmdb_id": 122917, "poster_url": "https://image.tmdb.org/t/p/w500/9z25Mcwzow5f0b5t8T7v7y1YF4.jpg", "release_year": 2014, "imdb_rating": 7.4, "old_msg_id": 2909},
        ]
    },
    # 8. MATRITSA
    {
        "name": "Matritsa (The Matrix)",
        "banner_poster": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg",
        "description": "Neo, Triniti va Morfeusning sun'iy intellekt va Matritsaga qarshi kurashi to'liq 4 qism.",
        "genres": "Ilmiy fantastika, Jangari",
        "rating": "8.5/10",
        "movies": [
            {"title": "Matritsa 1", "original_title": "The Matrix", "tmdb_id": 603, "poster_url": "https://image.tmdb.org/t/p/w500/f89U3ADr1oiB1s9GkdPOEpXUk5H.jpg", "release_year": 1999, "imdb_rating": 8.7, "old_msg_id": 8066},
            {"title": "Matritsa 2: Qayta yuklash", "original_title": "The Matrix Reloaded", "tmdb_id": 604, "poster_url": "https://image.tmdb.org/t/p/w500/9TGHDvWr2KPBCARAcRS9hkUhLLCu.jpg", "release_year": 2003, "imdb_rating": 7.2, "old_msg_id": 8068},
            {"title": "Matritsa 3: Revolyutsiya", "original_title": "The Matrix Revolutions", "tmdb_id": 605, "poster_url": "https://image.tmdb.org/t/p/w500/51tB59v1wGkOQ7j0M4eYkUq6G3V.jpg", "release_year": 2003, "imdb_rating": 6.8, "old_msg_id": 8070},
            {"title": "Matritsa 4: Qayta tirilish", "original_title": "The Matrix Resurrections", "tmdb_id": 624860, "poster_url": "https://image.tmdb.org/t/p/w500/8c4a8kE7PizaGQQvMiZtWau55of.jpg", "release_year": 2021, "imdb_rating": 5.7, "old_msg_id": 8072},
        ]
    },
    # 9. TERMINATOR
    {
        "name": "Terminator",
        "banner_poster": "https://image.tmdb.org/t/p/w500/hzXSE6MZ985AEft7Vf22Y7nrh5G.jpg",
        "description": "Arnold Shvarsnegger ishtirokidagi afsonaviy ilmiy-fantastik franchayz barcha qismlari.",
        "genres": "Ilmiy fantastika, Jangari",
        "rating": "8.5/10",
        "movies": [
            {"title": "Terminator 1", "original_title": "The Terminator", "tmdb_id": 218, "poster_url": "https://image.tmdb.org/t/p/w500/hzXSE6MZ985AEft7Vf22Y7nrh5G.jpg", "release_year": 1984, "imdb_rating": 8.1, "old_msg_id": 8116},
            {"title": "Terminator 2: Qiyomat kuni", "original_title": "Terminator 2: Judgment Day", "tmdb_id": 280, "poster_url": "https://image.tmdb.org/t/p/w500/5M0j0B18abtBI5P2nnQiYJKSu19.jpg", "release_year": 1991, "imdb_rating": 8.6, "old_msg_id": 8114},
            {"title": "Terminator 3: Mashinalar isyoni", "original_title": "Terminator 3: Rise of the Machines", "tmdb_id": 296, "poster_url": "https://image.tmdb.org/t/p/w500/vxiK1c67H8Z0jB7z2eYfNq8v2g6.jpg", "release_year": 2003, "imdb_rating": 6.3, "old_msg_id": 8118},
        ]
    },
    # 10. SHREK
    {
        "name": "Shrek",
        "banner_poster": "https://image.tmdb.org/t/p/w500/dyhaB19AIC4PkYQ2Y7YbpCNIIOx.jpg",
        "description": "Yashil maxluq Shrek va uning do'stlari sarguzashtlari barcha 4 qism to'liq.",
        "genres": "Animatsiya, Komediya, Oilaviy",
        "rating": "7.9/10",
        "movies": [
            {"title": "Shrek 1", "original_title": "Shrek", "tmdb_id": 808, "poster_url": "https://image.tmdb.org/t/p/w500/dyhaB19AIC4PkYQ2Y7YbpCNIIOx.jpg", "release_year": 2001, "imdb_rating": 7.9, "old_msg_id": 14488},
            {"title": "Shrek 2", "original_title": "Shrek 2", "tmdb_id": 809, "poster_url": "https://image.tmdb.org/t/p/w500/2yYP0PQjG8zV0TurmRxSSUrTXvw.jpg", "release_year": 2004, "imdb_rating": 7.3, "old_msg_id": 14490},
            {"title": "Shrek 3: Uchinchi", "original_title": "Shrek the Third", "tmdb_id": 810, "poster_url": "https://image.tmdb.org/t/p/w500/n5OcaP01z840M6c0K4bU5eU4yL.jpg", "release_year": 2007, "imdb_rating": 6.1, "old_msg_id": 14486},
            {"title": "Shrek 4: Abadiy baxt", "original_title": "Shrek Forever After", "tmdb_id": 10191, "poster_url": "https://image.tmdb.org/t/p/w500/bL8n7A6n5n4eL3q5e5i7x7e5y.jpg", "release_year": 2010, "imdb_rating": 6.3, "old_msg_id": 14484},
        ]
    },
    # 11. KUNG-FU PANDA
    {
        "name": "Kung-fu Panda",
        "banner_poster": "https://image.tmdb.org/t/p/w500/wWt4JYUtC6z4TpD24916qV7hM6.jpg",
        "description": "Ajdaho jangchisi Po va Qoyilmaqom beshlik sarguzashtlari barcha 4 qism to'liq.",
        "genres": "Animatsiya, Jangari, Komediya",
        "rating": "7.6/10",
        "movies": [
            {"title": "Kung Fu Panda 1", "original_title": "Kung Fu Panda", "tmdb_id": 9502, "poster_url": "https://image.tmdb.org/t/p/w500/wWt4JYUtC6z4TpD24916qV7hM6.jpg", "release_year": 2008, "imdb_rating": 7.6, "old_msg_id": 14492},
            {"title": "Kung Fu Panda 2", "original_title": "Kung Fu Panda 2", "tmdb_id": 49444, "poster_url": "https://image.tmdb.org/t/p/w500/mtqqD0022Y1Y9uNxjG1Xk4eUf6M.jpg", "release_year": 2011, "imdb_rating": 7.3, "old_msg_id": 14498},
            {"title": "Kung Fu Panda 3", "original_title": "Kung Fu Panda 3", "tmdb_id": 140300, "poster_url": "https://image.tmdb.org/t/p/w500/oajSLoGsqV4mN9k9j4fQk3H5v0e.jpg", "release_year": 2016, "imdb_rating": 7.1, "old_msg_id": 14494},
            {"title": "Kung Fu Panda 4", "original_title": "Kung Fu Panda 4", "tmdb_id": 1011985, "poster_url": "https://image.tmdb.org/t/p/w500/kDp1vUBnMpe8ak4rjgl3cLELqjU.jpg", "release_year": 2024, "imdb_rating": 6.8, "old_msg_id": 14496},
        ]
    },
    # 12. MUZLIK DAVRI
    {
        "name": "Muzlik davri (Ice Age)",
        "banner_poster": "https://image.tmdb.org/t/p/w500/zpaQwuwukPyz4a9u2gWfG34y7Q.jpg",
        "description": "Menni, Sid, Diego va yong'oqchi Skratning muzlik davridagi sarguzashtlari 1-5 qismlar.",
        "genres": "Animatsiya, Sarguzasht, Komediya",
        "rating": "7.5/10",
        "movies": [
            {"title": "Muzlik davri 1", "original_title": "Ice Age", "tmdb_id": 425, "poster_url": "https://image.tmdb.org/t/p/w500/zpaQwuwukPyz4a9u2gWfG34y7Q.jpg", "release_year": 2002, "imdb_rating": 7.5, "old_msg_id": 8311},
            {"title": "Muzlik davri 2: Jazirama issiq", "original_title": "Ice Age: The Meltdown", "tmdb_id": 950, "poster_url": "https://image.tmdb.org/t/p/w500/t0f0g2QhQxL3L3l8v7U3u9W2fK6.jpg", "release_year": 2006, "imdb_rating": 6.8, "old_msg_id": 8331},
            {"title": "Muzlik davri 3: Dinozavrlar asri", "original_title": "Ice Age: Dawn of the Dinosaurs", "tmdb_id": 8355, "poster_url": "https://image.tmdb.org/t/p/w500/1hQvF9H3Y8G7Q0R2a6F7t5v9a7P.jpg", "release_year": 2009, "imdb_rating": 6.9, "old_msg_id": 8329},
            {"title": "Muzlik davri 4: Ayro qit'alar", "original_title": "Ice Age: Continental Drift", "tmdb_id": 57800, "poster_url": "https://image.tmdb.org/t/p/w500/4s4H2l2eW7A0u3c8q1U4r5n9W7L.jpg", "release_year": 2012, "imdb_rating": 6.5, "old_msg_id": 8327},
            {"title": "Muzlik davri 5: Muqarrar to'qnashuv", "original_title": "Ice Age: Collision Course", "tmdb_id": 277834, "poster_url": "https://image.tmdb.org/t/p/w500/d3L1sL0n6qP0k5n9U8v5A7f2u3G.jpg", "release_year": 2016, "imdb_rating": 5.7, "old_msg_id": 8325},
        ]
    },
    # 13. MADAGASKAR
    {
        "name": "Madagaskar (Madagascar)",
        "banner_poster": "https://image.tmdb.org/t/p/w500/zByODJ4yYf8oQj8rYp6k0W2v7zD.jpg",
        "description": "Aleks, Marti, Gloriya, Melman va chaqqon pingvinlar jamoasi sarguzashtlari barcha filmlari.",
        "genres": "Animatsiya, Sarguzasht, Komediya",
        "rating": "7.0/10",
        "movies": [
            {"title": "Madagaskar 1", "original_title": "Madagascar", "tmdb_id": 953, "poster_url": "https://image.tmdb.org/t/p/w500/zByODJ4yYf8oQj8rYp6k0W2v7zD.jpg", "release_year": 2005, "imdb_rating": 6.9, "old_msg_id": 14502},
            {"title": "Madagaskar 2: Qochish", "original_title": "Madagascar: Escape 2 Africa", "tmdb_id": 10527, "poster_url": "https://image.tmdb.org/t/p/w500/uYf2f8g4y9p0U8q6r5m7z2y5e0V.jpg", "release_year": 2008, "imdb_rating": 6.6, "old_msg_id": 14506},
            {"title": "Madagaskar 3: Yevropa bo'ylab", "original_title": "Madagascar 3: Europe's Most Wanted", "tmdb_id": 80321, "poster_url": "https://image.tmdb.org/t/p/w500/f8s7w0n4y6k0q5k8m7l0p8z2e1V.jpg", "release_year": 2012, "imdb_rating": 6.8, "old_msg_id": 14504},
        ]
    }
]

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    for franchise in ALL_FRANCHISES:
        try:
            await migrate_franchise(client, franchise)
            await asyncio.sleep(2.5)
        except Exception as e:
            logger.error(f"Xatolik '{franchise['name']}' ni ko'chirishda: {e}", exc_info=True)

    await client.disconnect()
    logger.info("=== BARCHA FRANSHIZALAR VA FILMLAR KO'CHIRILDI! ===")

if __name__ == "__main__":
    asyncio.run(main())
