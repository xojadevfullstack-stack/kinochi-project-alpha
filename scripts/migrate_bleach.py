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

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logger = logging.getLogger("bleach_migration")

TARGET_SUPERGROUP = int(settings.AUTO_TOPIC_CHAT_ID)  # -1003847632555
TARGET_STORAGE = int(settings.STORAGE_CHANNEL_ID)    # -1003762157591
SOURCE_CHANNEL = -1003926001543

BLEACH_CONFIG = {
    "title": "Blich (Bleach)",
    "original_title": "Bleach",
    "tmdb_id": 30984,
    "poster_url": "https://image.tmdb.org/t/p/w500/ldLzOgDlAeoX3NgyhFQI1H3MXGk.jpg",
    "description": "Ichigo Kurosaki o'smirligidanoq sharpalarni ko'ra oladi. Bir kuni u o'lim xudosi — Shinigami Rukiya Kuchiki bilan uchrashadi. Rukiyaning kuchlari Ichigoga o'tadi va u insonlarni yovuz maxluqlar — Xolloulardan himoya qilishga majbur bo'ladi.",
    "imdb_rating": 8.2,
    "release_year": 2004,
    "status": "completed",
    "genres": "Anime, Jangari, Sarguzasht, G'ayritabiiy",
    "seasons": {
        1: list(range(1324, 1344)),  # 20 eps: 1324..1343
        2: list(range(1345, 1366))   # 21 eps: 1345..1365
    }
}

async def create_or_get_topic(client: TelegramClient, title: str) -> int:
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

async def fetch_poster_bytes(url: str) -> bytes | None:
    try:
        async with httpx.AsyncClient(timeout=15) as hclient:
            res = await hclient.get(url)
            if res.status_code == 200:
                return res.content
    except Exception as e:
        logger.warning(f"Poster yuklab olishda xatolik ({url}): {e}")
    return None

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    await client.get_dialogs()

    title = BLEACH_CONFIG["title"]
    logger.info("=" * 60)
    logger.info(f"=== BLEACH MIGRATSIYASI BOSHLANDI: {title} ===")
    logger.info("=" * 60)

    # 1. Topic yaratish
    topic_id = await create_or_get_topic(client, title)
    logger.info(f"Topic ochildi! Topic ID: {topic_id}")
    await asyncio.sleep(2.0)

    # 2. Topic Banner yuborish va qadash
    poster_bytes = await fetch_poster_bytes(BLEACH_CONFIG["poster_url"])
    caption_banner = (
        f"🎬 <b>{html.escape(title)}</b> ({BLEACH_CONFIG['release_year']})\n"
        f"🎭 <b>Janr:</b> {BLEACH_CONFIG['genres']}\n"
        f"⭐ <b>IMDb:</b> {BLEACH_CONFIG['imdb_rating']}/10\n"
        f"🇺🇿 <b>Tili:</b> O'zbek tilida\n\n"
        f"📖 <b>Tavsif:</b>\n{html.escape(BLEACH_CONFIG['description'])}\n\n"
        f"🍿 @kinochi_mvp_bot orqali yuklandi."
    )

    topic_banner_msg = None
    if poster_bytes:
        f_st = io.BytesIO(poster_bytes)
        f_st.name = "poster.jpg"
        while True:
            try:
                await client.send_file(TARGET_STORAGE, file=f_st, caption=caption_banner, parse_mode="html")
                break
            except FloodWaitError as fwe:
                await asyncio.sleep(fwe.seconds + 2)
        await asyncio.sleep(1.5)

        f_sg = io.BytesIO(poster_bytes)
        f_sg.name = "poster.jpg"
        while True:
            try:
                topic_banner_msg = await client.send_file(
                    TARGET_SUPERGROUP,
                    file=f_sg,
                    caption=caption_banner,
                    reply_to=topic_id,
                    parse_mode="html"
                )
                break
            except FloodWaitError as fwe:
                await asyncio.sleep(fwe.seconds + 2)
    else:
        while True:
            try:
                await client.send_message(TARGET_STORAGE, message=caption_banner, parse_mode="html")
                topic_banner_msg = await client.send_message(TARGET_SUPERGROUP, message=caption_banner, reply_to=topic_id, parse_mode="html")
                break
            except FloodWaitError as fwe:
                await asyncio.sleep(fwe.seconds + 2)

    await asyncio.sleep(1.5)
    if topic_banner_msg:
        try:
            from telethon.tl.functions.messages import UpdatePinnedMessageRequest
            await client(UpdatePinnedMessageRequest(
                peer=TARGET_SUPERGROUP,
                id=topic_banner_msg.id,
                silent=True
            ))
            logger.info(f"Banner topicga qadaldi (Msg ID: {topic_banner_msg.id})")
        except Exception as e:
            logger.warning(f"Bannerni qadashda ogohlantirish: {e}")

    await asyncio.sleep(1.5)

    # 3. DB da Source va Series yaratish
    async with async_session_factory() as session:
        src = SourceModel(
            name=title,
            type="superguruh",
            chat_id=TARGET_SUPERGROUP,
            topic_id=topic_id
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

        total_migrated = 0

        # 4. Mavsumlar va Qismlarni tartibli ko'chirish
        for s_num in sorted(BLEACH_CONFIG["seasons"].keys()):
            old_msg_ids = BLEACH_CONFIG["seasons"][s_num]
            logger.info(f"Bleach -> {s_num}-Mavsum: {len(old_msg_ids)} ta qism ko'chirilmoqda...")

            season_obj = SeasonModel(
                series_id=series_obj.id,
                season_number=s_num,
                title=f"{s_num}-Mavsum",
                status="completed",
                poster_url=BLEACH_CONFIG["poster_url"],
                episode_count=len(old_msg_ids)
            )
            session.add(season_obj)
            await session.flush()

            for ep_idx, old_ep_msg_id in enumerate(old_msg_ids, start=1):
                while True:
                    try:
                        ep_msg = await client.get_messages(SOURCE_CHANNEL, ids=old_ep_msg_id)
                        break
                    except FloodWaitError as fwe:
                        logger.warning(f"Flood wait {fwe.seconds}s...")
                        await asyncio.sleep(fwe.seconds + 2)

                if not ep_msg or not (ep_msg.video or ep_msg.document):
                    logger.warning(f"  [XATOLIK] Msg {old_ep_msg_id} topilmadi yoki media yo'q!")
                    continue

                display_code = f"S{s_num}-CH{ep_idx}"
                unique_code = uuid.uuid4().hex[:8]

                caption_ep = (
                    f"🎬 <b>{html.escape(title)}</b> | {s_num}-Mavsum, {ep_idx}-Qism\n"
                    f"🔢 <b>Kodi:</b> <code>{display_code}</code>\n"
                    f"🇺🇿 <b>Tili:</b> O'zbek tilida\n\n"
                    f"🍿 @kinochi_mvp_bot orqali yuklandi."
                )

                # Storage kanalga yuborish
                st_msg = None
                while True:
                    try:
                        st_msg = await client.send_file(
                            TARGET_STORAGE,
                            file=ep_msg.media,
                            caption=caption_ep,
                            parse_mode="html"
                        )
                        break
                    except FloodWaitError as fwe:
                        logger.warning(f"FloodWait storage: {fwe.seconds}s...")
                        await asyncio.sleep(fwe.seconds + 2)

                await asyncio.sleep(1.0)

                # Superguruh Topicga yuborish
                sg_msg = None
                while True:
                    try:
                        sg_msg = await client.send_file(
                            TARGET_SUPERGROUP,
                            file=ep_msg.media,
                            caption=caption_ep,
                            reply_to=topic_id,
                            parse_mode="html"
                        )
                        break
                    except FloodWaitError as fwe:
                        logger.warning(f"FloodWait topic: {fwe.seconds}s...")
                        await asyncio.sleep(fwe.seconds + 2)

                # DB ga yozish
                ep_obj = EpisodeModel(
                    season_id=season_obj.id,
                    episode_number=ep_idx,
                    code=unique_code,
                    display_code=display_code,
                    title=f"{ep_idx}-Qism",
                    duration=None,
                    source_message_id=sg_msg.id if sg_msg else None
                )
                session.add(ep_obj)
                await session.flush()

                trans_obj = EpisodeTranslationModel(
                    episode_id=ep_obj.id,
                    language="O'zbekcha",
                    storage_channel_message_id=st_msg.id if st_msg else None
                )
                session.add(trans_obj)

                total_migrated += 1
                logger.info(f"  [OK] Bleach S{s_num}E{ep_idx} (Topic: {sg_msg.id if sg_msg else '-'}, ST: {st_msg.id if st_msg else '-'})")
                await asyncio.sleep(1.2)

            await session.commit()
            logger.info(f"Bleach {s_num}-Mavsum commit qilindi!")

    logger.info(f"=== BLEACH TUGATILDI: jami {total_migrated} ta qism ko'chirildi ===")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
