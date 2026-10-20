import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
import asyncio
import os
import uuid
import html
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
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.models.source import SourceModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel
from app.infrastructure.db.models.page import PageModel, page_series_table

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logger = logging.getLogger("resume_bleach")

TARGET_SUPERGROUP = int(settings.AUTO_TOPIC_CHAT_ID)  # -1003847632555
TARGET_STORAGE = int(settings.STORAGE_CHANNEL_ID)    # -1003762157591
SOURCE_CHANNEL = -1003926001543
TOPIC_ID = 2729

BLEACH_CONFIG = {
    "title": "Blich (Bleach)",
    "original_title": "Bleach",
    "tmdb_id": 30984,
    "poster_url": "https://image.tmdb.org/t/p/w500/ldLzOgDlAeoX3NgyhFQI1H3MXGk.jpg",
    "description": "Ichigo Kurosaki o'smirligidanoq sharpalarni ko'ra oladi. Bir kuni u o'lim xudosi — Shinigami Rukiya Kuchiki bilan uchrashadi. Rukiyaning kuchlari Ichigoga o'tadi va u insonlarni yovuz maxluqlar — Xolloulardan himoya qilishga majbur bo'ladi.",
    "imdb_rating": 8.2,
    "release_year": 2004,
    "status": "completed",
    "genres": "Anime, Jangari, Sarguzasht, G'ayritabiiy"
}

# S1 existing 1..13:
# Topic: 2731..2743
# Storage: 1583..1595
EXISTING_S1 = [
    (1, 2731, 1583),
    (2, 2732, 1584),
    (3, 2733, 1585),
    (4, 2734, 1586),
    (5, 2735, 1587),
    (6, 2736, 1588),
    (7, 2737, 1589),
    (8, 2738, 1590),
    (9, 2739, 1591),
    (10, 2740, 1592),
    (11, 2741, 1593),
    (12, 2742, 1594),
    (13, 2743, 1595),
]

# S1 remaining 14..20:
REMAINING_S1 = [
    (14, 1337),
    (15, 1338),
    (16, 1339),
    (17, 1340),
    (18, 1341),
    (19, 1342),
    (20, 1343),
]

# S2 1..21:
SEASON_2_MSGS = [(idx, mid) for idx, mid in enumerate(range(1345, 1366), start=1)]

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    await client.get_dialogs()

    title = BLEACH_CONFIG["title"]
    logger.info(f"=== BLEACH TOPIC {TOPIC_ID} DAVOM ETTIRILMOQDA ===")

    async with async_session_factory() as session:
        # Source va Series yaratish
        src = SourceModel(
            name=title,
            type="superguruh",
            chat_id=TARGET_SUPERGROUP,
            topic_id=TOPIC_ID
        )
        session.add(src)
        await session.flush()

        series_obj = SeriesModel(
            title=title,
            description=BLEACH_CONFIG["description"],
            status=BLEACH_CONFIG["status"],
            publish_status="published",
            is_18_plus=False,
            imdb_rating=BLEACH_CONFIG["imdb_rating"],
            release_year=BLEACH_CONFIG["release_year"],
            tmdb_id=BLEACH_CONFIG["tmdb_id"],
            poster_url=BLEACH_CONFIG["poster_url"],
            source_id=src.id,
            source_type="superguruh",
            custom_source_name="Kinochi @kinochi_mvp_bot"
        )
        session.add(series_obj)
        await session.flush()
        await session.execute(page_series_table.insert().values(series_id=series_obj.id, page_id=1))

        # 1-MAVSUM (20 ta qism)
        s1_obj = SeasonModel(
            series_id=series_obj.id,
            season_number=1,
            title="1-Mavsum",
            status="completed",
            poster_url=BLEACH_CONFIG["poster_url"],
            episode_count=20
        )
        session.add(s1_obj)
        await session.flush()

        # Mavjud 1..13 qismlarni DB ga kiritish
        for ep_num, top_id, st_id in EXISTING_S1:
            disp = f"S1-CH{ep_num}"
            code = uuid.uuid4().hex[:8]
            ep_obj = EpisodeModel(
                season_id=s1_obj.id,
                episode_number=ep_num,
                code=code,
                display_code=disp,
                title=f"{ep_num}-Qism",
                source_message_id=top_id
            )
            session.add(ep_obj)
            await session.flush()
            tr_obj = EpisodeTranslationModel(
                episode_id=ep_obj.id,
                language="O'zbekcha",
                storage_channel_message_id=st_id
            )
            session.add(tr_obj)
            logger.info(f"  [DB LINK] S1E{ep_num} -> Topic {top_id}, Storage {st_id}")

        # Qolgan 14..20 qismlarni yuborish
        for ep_num, old_mid in REMAINING_S1:
            ep_msg = await client.get_messages(SOURCE_CHANNEL, ids=old_mid)
            disp = f"S1-CH{ep_num}"
            code = uuid.uuid4().hex[:8]
            caption = (
                f"🎬 <b>{html.escape(title)}</b> | 1-Mavsum, {ep_num}-Qism\n"
                f"🔢 <b>Kodi:</b> <code>{disp}</code>\n"
                f"🇺🇿 <b>Tili:</b> O'zbek tilida\n\n"
                f"🍿 @kinochi_mvp_bot orqali yuklandi."
            )
            # Storage
            while True:
                try:
                    st_msg = await client.send_file(TARGET_STORAGE, file=ep_msg.media, caption=caption, parse_mode="html")
                    break
                except FloodWaitError as fwe:
                    await asyncio.sleep(fwe.seconds + 2)
            await asyncio.sleep(1.0)
            # Topic
            while True:
                try:
                    top_msg = await client.send_file(TARGET_SUPERGROUP, file=ep_msg.media, caption=caption, reply_to=TOPIC_ID, parse_mode="html")
                    break
                except FloodWaitError as fwe:
                    await asyncio.sleep(fwe.seconds + 2)

            ep_obj = EpisodeModel(
                season_id=s1_obj.id,
                episode_number=ep_num,
                code=code,
                display_code=disp,
                title=f"{ep_num}-Qism",
                source_message_id=top_msg.id
            )
            session.add(ep_obj)
            await session.flush()
            tr_obj = EpisodeTranslationModel(
                episode_id=ep_obj.id,
                language="O'zbekcha",
                storage_channel_message_id=st_msg.id
            )
            session.add(tr_obj)
            logger.info(f"  [SENT] S1E{ep_num} -> Topic {top_msg.id}, Storage {st_msg.id}")
            await asyncio.sleep(1.2)

        await session.commit()
        logger.info("Bleach 1-Mavsum to'liq yakunlandi va commit qilindi!")

        # 2-MAVSUM (21 ta qism)
        s2_obj = SeasonModel(
            series_id=series_obj.id,
            season_number=2,
            title="2-Mavsum",
            status="completed",
            poster_url=BLEACH_CONFIG["poster_url"],
            episode_count=21
        )
        session.add(s2_obj)
        await session.flush()

        for ep_num, old_mid in SEASON_2_MSGS:
            ep_msg = await client.get_messages(SOURCE_CHANNEL, ids=old_mid)
            disp = f"S2-CH{ep_num}"
            code = uuid.uuid4().hex[:8]
            caption = (
                f"🎬 <b>{html.escape(title)}</b> | 2-Mavsum, {ep_num}-Qism\n"
                f"🔢 <b>Kodi:</b> <code>{disp}</code>\n"
                f"🇺🇿 <b>Tili:</b> O'zbek tilida\n\n"
                f"🍿 @kinochi_mvp_bot orqali yuklandi."
            )
            # Storage
            while True:
                try:
                    st_msg = await client.send_file(TARGET_STORAGE, file=ep_msg.media, caption=caption, parse_mode="html")
                    break
                except FloodWaitError as fwe:
                    await asyncio.sleep(fwe.seconds + 2)
            await asyncio.sleep(1.0)
            # Topic
            while True:
                try:
                    top_msg = await client.send_file(TARGET_SUPERGROUP, file=ep_msg.media, caption=caption, reply_to=TOPIC_ID, parse_mode="html")
                    break
                except FloodWaitError as fwe:
                    await asyncio.sleep(fwe.seconds + 2)

            ep_obj = EpisodeModel(
                season_id=s2_obj.id,
                episode_number=ep_num,
                code=code,
                display_code=disp,
                title=f"{ep_num}-Qism",
                source_message_id=top_msg.id
            )
            session.add(ep_obj)
            await session.flush()
            tr_obj = EpisodeTranslationModel(
                episode_id=ep_obj.id,
                language="O'zbekcha",
                storage_channel_message_id=st_msg.id
            )
            session.add(tr_obj)
            logger.info(f"  [SENT] S2E{ep_num} -> Topic {top_msg.id}, Storage {st_msg.id}")
            await asyncio.sleep(1.2)

        await session.commit()
        logger.info("Bleach 2-Mavsum to'liq yakunlandi va commit qilindi!")

    await client.disconnect()
    logger.info("=== BLEACH RESUME TO'LIQ VA MUVAFFAQIYATLI YAKUNLANDI! ===")

if __name__ == "__main__":
    asyncio.run(main())
