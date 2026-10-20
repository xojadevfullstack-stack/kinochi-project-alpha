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
import json
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
logger = logging.getLogger("pusu_migration")

TARGET_SUPERGROUP = int(settings.AUTO_TOPIC_CHAT_ID)  # -1003847632555
TARGET_STORAGE = int(settings.STORAGE_CHANNEL_ID)    # -1003762157591
CH_SOURCES = [-1003926001543, -1003941035700]

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

async def get_msg_from_sources(client: TelegramClient, msg_id: int):
    for ch in CH_SOURCES:
        while True:
            try:
                m = await client.get_messages(ch, ids=msg_id)
                if m and (m.video or m.document):
                    return m
                break
            except FloodWaitError as fwe:
                logger.warning(f"Flood wait {fwe.seconds}s on get_messages")
                await asyncio.sleep(fwe.seconds + 2)
            except Exception:
                break
    return None

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    await client.get_dialogs()

    config_path = os.path.join(os.path.dirname(__file__), "kurtlar_pusu_config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        cfg = json.load(f)

    title = cfg["title"]
    original_title = cfg["original_title"]
    tmdb_id = cfg["tmdb_id"]
    poster_url = cfg["poster_url"]
    description = cfg["description"]
    imdb_rating = cfg["imdb_rating"]
    release_year = cfg["release_year"]
    status = cfg["status"]
    genres = cfg["genres"]
    seasons_data = cfg["seasons_data"]

    logger.info("==================================================")
    logger.info(f"=== BOSHlandi: {title} ({release_year}) — 200 ta qism ===")
    logger.info("==================================================")

    # 1. Topic ochish
    topic_id = await create_or_get_topic(client, title)
    logger.info(f"Topic ochildi! Topic ID: {topic_id}")
    await asyncio.sleep(2.0)

    # 2. Topic Banner yuborish va qadash
    poster_bytes = await fetch_poster_bytes(poster_url)
    caption_banner = (
        f"🎬 <b>{html.escape(title)}</b> ({release_year})\n"
        f"🎭 <b>Janr:</b> {genres}\n"
        f"⭐ <b>IMDb:</b> {imdb_rating}/10\n"
        f"🇺🇿 <b>Tili:</b> O'zbek tilida\n\n"
        f"📖 <b>Tavsif:</b>\n{html.escape(description[:700])}\n\n"
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
            description=description,
            status=status,
            publish_status="published",
            is_18_plus=False,
            imdb_rating=imdb_rating,
            release_year=release_year,
            tmdb_id=tmdb_id,
            poster_url=poster_url,
            source_id=src.id,
            source_type="superguruh",
            custom_source_name="Kinochi @kinochi_mvp_bot"
        )
        session.add(series_obj)
        await session.flush()

        total_migrated = 0

        # 4. Mavsumlar va Qismlarni tartibli ko'chirish
        for s_num_str in sorted(seasons_data.keys(), key=lambda x: int(x)):
            s_num = int(s_num_str)
            old_msg_ids = seasons_data[s_num_str]
            logger.info(f"{title} -> {s_num}-Mavsum: {len(old_msg_ids)} ta qism ko'chirilmoqda...")

            season_obj = SeasonModel(
                series_id=series_obj.id,
                season_number=s_num,
                title=f"{s_num}-Mavsum",
                status="completed" if status == "completed" else "ongoing",
                poster_url=poster_url,
                episode_count=len(old_msg_ids)
            )
            session.add(season_obj)
            await session.flush()

            for ep_idx, old_ep_msg_id in enumerate(old_msg_ids, start=1):
                ep_msg = await get_msg_from_sources(client, old_ep_msg_id)
                if not ep_msg:
                    logger.warning(f"  [XATOLIK] Msg {old_ep_msg_id} topilmadi!")
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
                logger.info(f"  [OK] {title} S{s_num}E{ep_idx} (Topic: {sg_msg.id if sg_msg else '-'}, ST: {st_msg.id if st_msg else '-'})")
                await asyncio.sleep(1.2)

            await session.commit()
            logger.info(f"{title} {s_num}-Mavsum commit qilindi!")

    await client.disconnect()
    logger.info(f"=== {title} TO'LIQ KO'CHIRILDI: jami {total_migrated} ta qism! ===")

if __name__ == "__main__":
    asyncio.run(main())
