import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import asyncio
import os
import random
import uuid
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
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
logger = logging.getLogger("masterpiece_migration")

TARGET_SUPERGROUP = int(settings.AUTO_TOPIC_CHAT_ID)  # -1003847632555
TARGET_STORAGE = int(settings.STORAGE_CHANNEL_ID)    # -1003762157591

CH_PRIMARY = -1003926001543
CH_SECONDARY = -1003941035700

MASTERPIECES = [
    # 1. Jahon Kinosining Eng Sara Shedevrlari
    {
        "title": "Jang Klubi",
        "original_title": "Fight Club",
        "release_year": 1999,
        "tmdb_id": 550,
        "imdb_rating": 8.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/66RvLrRJTm4J8l3uHXWF09AICol.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 25928
    },
    {
        "title": "Interstellar (1-qism)",
        "original_title": "Interstellar (Part 1)",
        "release_year": 2014,
        "tmdb_id": 157336,
        "imdb_rating": 8.7,
        "poster_url": "https://image.tmdb.org/t/p/w500/vReLRjDV9XPhiOSEW7QWow4DXwf.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 27519
    },
    {
        "title": "Interstellar (2-qism)",
        "original_title": "Interstellar (Part 2)",
        "release_year": 2014,
        "tmdb_id": 157336,
        "imdb_rating": 8.7,
        "poster_url": "https://image.tmdb.org/t/p/w500/vReLRjDV9XPhiOSEW7QWow4DXwf.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 27519
    },
    {
        "title": "Titanik (1-qism)",
        "original_title": "Titanic (Part 1)",
        "release_year": 1997,
        "tmdb_id": 597,
        "imdb_rating": 7.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/r3sYKBtoNHPyS9vkaA8dJyh8grG.jpg",
        "source_chat_id": CH_SECONDARY,
        "source_msg_id": 938
    },
    {
        "title": "Titanik (2-qism)",
        "original_title": "Titanic (Part 2)",
        "release_year": 1997,
        "tmdb_id": 597,
        "imdb_rating": 7.9,
        "poster_url": "https://image.tmdb.org/t/p/w500/r3sYKBtoNHPyS9vkaA8dJyh8grG.jpg",
        "source_chat_id": CH_SECONDARY,
        "source_msg_id": 940
    },
    {
        "title": "Anora",
        "original_title": "Anora",
        "release_year": 2024,
        "tmdb_id": 1064213,
        "imdb_rating": 7.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/lA51ZjHnbVmReYeFBAt2T0LPHAO.jpg",
        "source_chat_id": CH_SECONDARY,
        "source_msg_id": 955
    },
    {
        "title": "La'natlanganlar oroli",
        "original_title": "Shutter Island",
        "release_year": 2010,
        "tmdb_id": 11324,
        "imdb_rating": 8.2,
        "poster_url": "https://image.tmdb.org/t/p/w500/3UVMyefkUBiktshtKIEnNXvOFKH.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 8213
    },
    {
        "title": "Faun Labirinti",
        "original_title": "Pan's Labyrinth",
        "release_year": 2006,
        "tmdb_id": 1417,
        "imdb_rating": 8.2,
        "poster_url": "https://image.tmdb.org/t/p/w500/h2oVVLTa2eQmhEfwuVlG1VUEuuz.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 8101
    },
    {
        "title": "Donni Darko",
        "original_title": "Donnie Darko",
        "release_year": 2001,
        "tmdb_id": 141,
        "imdb_rating": 8.0,
        "poster_url": "https://image.tmdb.org/t/p/w500/xIHM3COCyrDjWVoK1j7ELkuMfrh.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 6357
    },
    {
        "title": "Jentelmenlar",
        "original_title": "The Gentlemen",
        "release_year": 2020,
        "tmdb_id": 522627,
        "imdb_rating": 7.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/vWxVVECgYDPSg5o0Rhw5u7KFa7X.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 5843
    },
    {
        "title": "Velosiped o‘g‘rilari",
        "original_title": "Bicycle Thieves",
        "release_year": 1948,
        "tmdb_id": 5156,
        "imdb_rating": 8.2,
        "poster_url": "https://image.tmdb.org/t/p/w500/sG8NMNWbP7lrf3S1Pk3Bai40Ctz.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 3879
    },
    {
        "title": "Bir vaqtlar Anadoluda",
        "original_title": "Once Upon a Time in Anatolia",
        "release_year": 2011,
        "tmdb_id": 71880,
        "imdb_rating": 7.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/bl4eyeZ1wKkWMsyivPGh3Pw12vn.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 4957
    },
    {
        "title": "12 Stul",
        "original_title": "The Twelve Chairs",
        "release_year": 1971,
        "tmdb_id": 41539,
        "imdb_rating": 8.1,
        "poster_url": "https://image.tmdb.org/t/p/w500/eoq8H8KfQWT5kiX5uVjdAT1wE6x.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 3112
    },
    {
        "title": "Jajji Guvoh",
        "original_title": "Laapataa Ladies",
        "release_year": 2024,
        "tmdb_id": 1111622,
        "imdb_rating": 8.5,
        "poster_url": "https://image.tmdb.org/t/p/w500/bwULdk1aKiWABzwlj4CK7jKz9hI.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 2159
    },

    # 2. Pixar & Disney Oskar G'oliblari
    {
        "title": "Vall-i",
        "original_title": "WALL-E",
        "release_year": 2008,
        "tmdb_id": 10681,
        "imdb_rating": 8.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/uR79KoBwDMz1qbxwmuY0bpcDYtf.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 2086
    },
    {
        "title": "Up — Tepaga",
        "original_title": "Up",
        "release_year": 2009,
        "tmdb_id": 14160,
        "imdb_rating": 8.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/47DEnHvvLCOPLPG7QpM8mXLCJG5.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 2087
    },
    {
        "title": "Kokoning siri",
        "original_title": "Coco",
        "release_year": 2017,
        "tmdb_id": 354912,
        "imdb_rating": 8.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/jvYsGaUqN8ymH696kRfVJjJ3GIl.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 2088
    },
    {
        "title": "Ratatuy",
        "original_title": "Ratatouille",
        "release_year": 2007,
        "tmdb_id": 2062,
        "imdb_rating": 8.1,
        "poster_url": "https://image.tmdb.org/t/p/w500/ojJnDAWLy656Lx9ksj6nP7ubQjq.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 2089
    },

    # 3. Superqahramonlar va Jangari Qo'shimchalar
    {
        "title": "Qora Pantera",
        "original_title": "Black Panther",
        "release_year": 2018,
        "tmdb_id": 284054,
        "imdb_rating": 7.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/ndpwgAANbZSMwgTcxmQ7o4SKDsd.jpg",
        "source_chat_id": CH_SECONDARY,
        "source_msg_id": 3893
    },
    {
        "title": "Kapitan Amerika: Yangi dunyo",
        "original_title": "Captain America: Brave New World",
        "release_year": 2025,
        "tmdb_id": 822119,
        "imdb_rating": 6.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/bljRQO5fTGen0qRV7KuPRXIdRGx.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 2151
    },
    {
        "title": "Supermen (2025)",
        "original_title": "Superman",
        "release_year": 2025,
        "tmdb_id": 1064028,
        "imdb_rating": 7.5,
        "poster_url": "https://image.tmdb.org/t/p/w500/oGoQ5W5Zxo55hbqCu1PsqEmQJIX.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 2782
    },
    {
        "title": "Terminator 4: Najotkorning kelishi",
        "original_title": "Terminator Salvation",
        "release_year": 2009,
        "tmdb_id": 534,
        "imdb_rating": 6.5,
        "poster_url": "https://image.tmdb.org/t/p/w500/irfM3I3nm9aVRN09HGQc18TJOyP.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 8091
    },
    {
        "title": "Terminator 5: Genezis",
        "original_title": "Terminator Genisys",
        "release_year": 2015,
        "tmdb_id": 87101,
        "imdb_rating": 6.3,
        "poster_url": "https://image.tmdb.org/t/p/w500/eMUscX52jUbNC1xn4WJthJDUQNq.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 8089
    },

    # 4. Mualliflik Anime Durdonalari (Makoto Shinkai, Ghibli, Mustaqil)
    {
        "title": "Ovoz shakli",
        "original_title": "A Silent Voice",
        "release_year": 2016,
        "tmdb_id": 378064,
        "imdb_rating": 8.1,
        "poster_url": "https://image.tmdb.org/t/p/w500/c0Gv8xTSEmIcQPxbhINKvkbJO8s.jpg",
        "source_chat_id": CH_SECONDARY,
        "source_msg_id": 1545
    },
    {
        "title": "Sening isming",
        "original_title": "Your Name.",
        "release_year": 2016,
        "tmdb_id": 372058,
        "imdb_rating": 8.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/iH2WDCYLIUjc7oPWRT7Kxgxza6k.jpg",
        "source_chat_id": CH_SECONDARY,
        "source_msg_id": 1549
    },
    {
        "title": "Yonar qo'ng'izlar qabristoni",
        "original_title": "Grave of the Fireflies",
        "release_year": 1988,
        "tmdb_id": 12477,
        "imdb_rating": 8.5,
        "poster_url": "https://image.tmdb.org/t/p/w500/r25pROjJSaORRtyCkbbrEp9kMaL.jpg",
        "source_chat_id": CH_SECONDARY,
        "source_msg_id": 1553
    },
    {
        "title": "Ruhlar olami",
        "original_title": "Spirited Away",
        "release_year": 2001,
        "tmdb_id": 129,
        "imdb_rating": 8.6,
        "poster_url": "https://image.tmdb.org/t/p/w500/txaVo4whnSduKuczZiJexhLDVQC.jpg",
        "source_chat_id": CH_SECONDARY,
        "source_msg_id": 1557
    },
    {
        "title": "Sening oshqozon osti bezingni yemoqchiman",
        "original_title": "I Want to Eat Your Pancreas",
        "release_year": 2018,
        "tmdb_id": 504253,
        "imdb_rating": 8.0,
        "poster_url": "https://image.tmdb.org/t/p/w500/avj8X4mamOl9Co9rARHwivaP2Td.jpg",
        "source_chat_id": CH_SECONDARY,
        "source_msg_id": 1561
    },
    {
        "title": "Bolakay, ko‘rsichqon, tulki va ot",
        "original_title": "The Boy, the Mole, the Fox and the Horse",
        "release_year": 2022,
        "tmdb_id": 995133,
        "imdb_rating": 7.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/jL39De3a2Ab8y0TsmawvHZaouTE.jpg",
        "source_chat_id": CH_SECONDARY,
        "source_msg_id": 1565
    },
    {
        "title": "KIKI: Yetkazib berish xizmati",
        "original_title": "Kiki's Delivery Service",
        "release_year": 1989,
        "tmdb_id": 16859,
        "imdb_rating": 7.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/ufr0XB3QSLZCwrrIyQSVATp9jCU.jpg",
        "source_chat_id": CH_SECONDARY,
        "source_msg_id": 1570
    },
    {
        "title": "Nafis so‘zlar bog‘i",
        "original_title": "The Garden of Words",
        "release_year": 2013,
        "tmdb_id": 198375,
        "imdb_rating": 7.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/mwTqhLpm3TISNm5FJL58b7NHq8b.jpg",
        "source_chat_id": CH_SECONDARY,
        "source_msg_id": 1574
    },
    {
        "title": "Suzume",
        "original_title": "Suzume",
        "release_year": 2022,
        "tmdb_id": 916224,
        "imdb_rating": 7.6,
        "poster_url": "https://image.tmdb.org/t/p/w500/6YkQu9TRAsZhGGh0t7U7DP1BuhQ.jpg",
        "source_chat_id": CH_SECONDARY,
        "source_msg_id": 1578
    },
    {
        "title": "Josee: yo‘lbars va baliq",
        "original_title": "Josee, the Tiger and the Fish",
        "release_year": 2020,
        "tmdb_id": 652837,
        "imdb_rating": 7.6,
        "poster_url": "https://image.tmdb.org/t/p/w500/AdS4ugysKcsKkSm59OfjTtQ22Jg.jpg",
        "source_chat_id": CH_SECONDARY,
        "source_msg_id": 1582
    },
    {
        "title": "Yozgi tunnel, xayrlashuv eshigi",
        "original_title": "The Tunnel to Summer, the Exit of Goodbyes",
        "release_year": 2022,
        "tmdb_id": 916192,
        "imdb_rating": 7.2,
        "poster_url": "https://image.tmdb.org/t/p/w500/5AGA6pbBKXZTI8k1c6odx30JuQR.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 1278
    },
    {
        "title": "Aura: Koga Maryuinning so‘nggi jangi",
        "original_title": "Aura: Koga Maryuin's Last War",
        "release_year": 2013,
        "tmdb_id": 206487,
        "imdb_rating": 7.0,
        "poster_url": "https://image.tmdb.org/t/p/w500/mIrmu83OaTmxYhZQUSjQedtz5Cs.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 1279
    },
    {
        "title": "Shamol ko‘tarilmoqda",
        "original_title": "The Wind Rises",
        "release_year": 2013,
        "tmdb_id": 149870,
        "imdb_rating": 7.7,
        "poster_url": "https://image.tmdb.org/t/p/w500/hHzIDZUnhgsmNgbZlrH92fe5mWG.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 1321
    },
    {
        "title": "Mortal Kombat: Chayonning qasosi",
        "original_title": "Mortal Kombat Legends: Scorpion's Revenge",
        "release_year": 2020,
        "tmdb_id": 664767,
        "imdb_rating": 7.4,
        "poster_url": "https://image.tmdb.org/t/p/w500/t4blfxA4rIqUD49gyU6txgeaRT9.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 1322
    },
    {
        "title": "Seni doim sevganman",
        "original_title": "I've Always Liked You",
        "release_year": 2016,
        "tmdb_id": 393764,
        "imdb_rating": 6.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/nUOuBg0OAUuJIgyYl35rQ3uxQCa.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 1377
    },
    {
        "title": "Arra odam: Reze hikoyasi",
        "original_title": "Chainsaw Man – The Movie: Reze Arc",
        "release_year": 2025,
        "tmdb_id": 1218925,
        "imdb_rating": 8.0,
        "poster_url": "https://image.tmdb.org/t/p/w500/pHyxb2RV5wLlboAwm9ZJ9qTVEDw.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 1378
    },
    {
        "title": "Jodugarlar jangi 0",
        "original_title": "Jujutsu Kaisen 0",
        "release_year": 2021,
        "tmdb_id": 810693,
        "imdb_rating": 7.8,
        "poster_url": "https://image.tmdb.org/t/p/w500/rzi4VAYuT3bQDDUtomXQsxE71db.jpg",
        "source_chat_id": CH_PRIMARY,
        "source_msg_id": 1393
    }
]

async def create_single_topic(client: TelegramClient, title: str) -> int:
    from telethon.tl.functions.messages import CreateForumTopicRequest
    peer = await client.get_input_entity(TARGET_SUPERGROUP)
    r_id = random.randint(1, 2**31 - 1)
    while True:
        try:
            res = await client(CreateForumTopicRequest(
                peer=peer,
                title=title[:128],
                random_id=r_id
            ))
            break
        except FloodWaitError as fwe:
            logger.warning(f"Flood wait {fwe.seconds}s on create topic")
            await asyncio.sleep(fwe.seconds + 2)
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

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    await client.get_dialogs()

    logger.info(f"=== BOSHlandi: {len(MASTERPIECES)} ta mustaqil durdona va anime kinolari ko'chirilmoqda ===")

    for idx, item in enumerate(MASTERPIECES, start=1):
        title = item["title"]
        safe_title = title.encode('ascii', errors='replace').decode('ascii')
        logger.info(f"[{idx}/{len(MASTERPIECES)}] '{safe_title}'...")

        try:
            # 1. Create Topic in supergroup
            topic_id = await create_single_topic(client, title)
            await asyncio.sleep(1.5)

            # 2. Database Insert / Check
            async with async_session_factory() as session:
                q = select(MovieModel).where(MovieModel.title == title)
                res = await session.execute(q)
                movie = res.scalars().first()

                if not movie and item.get("tmdb_id") and "qism" not in title.lower():
                    q2 = select(MovieModel).where(MovieModel.tmdb_id == item["tmdb_id"])
                    res2 = await session.execute(q2)
                    movie = res2.scalars().first()

                if not movie:
                    movie = MovieModel(
                        title=title,
                        original_title=item.get("original_title"),
                        release_year=item.get("release_year"),
                        tmdb_id=item.get("tmdb_id"),
                        imdb_rating=item.get("imdb_rating"),
                        poster_url=item.get("poster_url"),
                        source_type="superguruh",
                        source_chat_id=TARGET_SUPERGROUP,
                        source_topic_id=topic_id,
                        code=uuid.uuid4().hex[:8],
                        publish_status="published",
                        is_18_plus=False,
                        custom_source_name="Kinochi @kinochi_mvp_bot"
                    )
                    session.add(movie)
                    await session.commit()
                    await session.refresh(movie)
                else:
                    movie.source_type = "superguruh"
                    movie.source_chat_id = TARGET_SUPERGROUP
                    movie.source_topic_id = topic_id
                    if item.get("poster_url"):
                        movie.poster_url = item["poster_url"]
                    if item.get("imdb_rating"):
                        movie.imdb_rating = item["imdb_rating"]
                    if item.get("release_year"):
                        movie.release_year = item["release_year"]
                    await session.commit()
                m_id = movie.id
                m_code = movie.code

            # 3. Forward Video to topic
            source_ch = item["source_chat_id"]
            source_mid = item["source_msg_id"]

            try:
                src_msg = await client.get_messages(source_ch, ids=source_mid)
            except FloodWaitError as fwe:
                await asyncio.sleep(fwe.seconds + 2)
                src_msg = await client.get_messages(source_ch, ids=source_mid)

            if not src_msg or not (src_msg.video or src_msg.document):
                logger.warning(f"  [XATOLIK] Msg ID {source_mid} da video topilmadi!")
                continue

            caption_txt = (
                f"🍿 <b>{title}</b> ({item.get('release_year')})\n\n"
                f"🔑 <b>Film kodi:</b> <code>{m_code}</code>\n"
                f"⭐ <b>IMDb:</b> {item.get('imdb_rating')}\n\n"
                f"🤖 Bot orqali tomosha qiling: @kinochi_mvp_bot"
            )

            sent_msg = None
            for attempt in range(5):
                try:
                    sent_msg = await client.send_file(
                        TARGET_SUPERGROUP,
                        file=src_msg.media,
                        caption=caption_txt,
                        reply_to=topic_id,
                        parse_mode="html"
                    )
                    break
                except FloodWaitError as fwe:
                    logger.warning(f"Flood wait {fwe.seconds}s...")
                    await asyncio.sleep(fwe.seconds + 2)
                except Exception as e:
                    logger.error(f"Xato yuborishda: {e}")
                    await asyncio.sleep(2.0)

            if not sent_msg:
                logger.error(f"Video topicga yuborilmadi: {title}")
                continue

            logger.info(f"  [OK] '{safe_title}' Topic {topic_id} ga uzatildi (Msg ID: {sent_msg.id})!")

            # 4. Wait for auto_index debounce
            indexed = False
            for _ in range(5):
                await asyncio.sleep(2.5)
                async with async_session_factory() as session:
                    res_t = await session.execute(
                        select(MovieTranslationModel).where(MovieTranslationModel.movie_id == m_id)
                    )
                    trans = res_t.scalars().first()
                    if trans and trans.storage_channel_message_id:
                        logger.info(f"  [BOT INDEXED] Movie ID {m_id} -> ST msg {trans.storage_channel_message_id}")
                        indexed = True
                        break

            # 5. Fallback directly to storage channel if not indexed
            if not indexed:
                logger.warning(f"  Bot indekslamadi. Fallback sifatida Storage kanalga nusxalanmoqda...")
                try:
                    storage_msg = await client.send_file(
                        TARGET_STORAGE,
                        file=src_msg.media,
                        caption=caption_txt,
                        parse_mode="html"
                    )
                    async with async_session_factory() as session:
                        res_trans = await session.execute(
                            select(MovieTranslationModel).where(MovieTranslationModel.movie_id == m_id)
                        )
                        trans_obj = res_trans.scalar_one_or_none()
                        if trans_obj:
                            trans_obj.storage_channel_message_id = storage_msg.id
                        else:
                            trans_obj = MovieTranslationModel(
                                movie_id=m_id,
                                language="O'zbekcha",
                                storage_channel_message_id=storage_msg.id
                            )
                            session.add(trans_obj)
                        await session.commit()
                    logger.info(f"  [Fallback OK] Storage kanalga nusxalandi (Msg ID: {storage_msg.id}).")
                except Exception as e:
                    logger.error(f"  Fallback nusxalashda xato: {e}")

            await asyncio.sleep(2.0)

        except Exception as e:
            logger.error(f"Xatolik '{safe_title}' ni ko'chirishda: {e}", exc_info=True)

    await client.disconnect()
    logger.info("=== BARCHA DURDONA KINOLAR KO'CHIRILDI! ===")

if __name__ == "__main__":
    asyncio.run(main())
