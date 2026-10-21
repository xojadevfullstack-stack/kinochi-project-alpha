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

# Path setup
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
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel, series_category_table
from app.infrastructure.db.models.source import SourceModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel
from app.infrastructure.db.models.category import CategoryModel
from sqlalchemy import select, insert
from telethon.tl.functions.messages import CreateForumTopicRequest, UpdatePinnedMessageRequest

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logger = logging.getLogger("got_migrator")

TARGET_SUPERGROUP = int(settings.AUTO_TOPIC_CHAT_ID)  # -1003847632555
TARGET_STORAGE = int(settings.STORAGE_CHANNEL_ID)    # -1003762157591
OLD_CHAT = -1003941035700
OLD_TOPIC_ID = 525

# All 73 episodes across 8 seasons in Old Chat Topic 525
GOT_SEASONS = {
    1: [528, 529, 530, 531, 532, 533, 534, 535, 536, 537],
    2: [548, 549, 550, 551, 552, 553, 554, 555, 556, 557],
    3: [588, 589, 590, 591, 592, 593, 594, 595, 596, 597],
    4: [608, 609, 610, 611, 612, 613, 614, 615, 616, 617],
    5: [628, 629, 630, 631, 632, 633, 634, 635, 636, 637],
    6: [648, 649, 650, 651, 652, 653, 654, 655, 656, 657],
    7: [668, 669, 670, 671, 672, 673, 674],
    8: [682, 683, 684, 685, 686, 687]
}

async def fetch_poster_bytes(url: str) -> bytes | None:
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as hclient:
            res = await hclient.get(url)
            if res.status_code == 200:
                return res.content
    except Exception as e:
        logger.warning(f"Poster yuklab olishda xatolik ({url}): {e}")
    return None

async def create_or_find_topic(client: TelegramClient, title: str) -> int:
    # First check existing recent topics in TARGET_SUPERGROUP
    async for m in client.iter_messages(TARGET_SUPERGROUP, limit=100):
        if getattr(m, 'action', None) and type(m.action).__name__ == 'MessageActionTopicCreate':
            if m.action.title.strip() == title.strip():
                logger.info(f"Mavjud topic topildi: '{title}' (ID: {m.id})")
                return m.id

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

    title = "Taxtlar oʻyini"
    original_title = "Game of Thrones"
    release_year = 2011
    imdb_rating = 9.2
    tmdb_id = 1399
    status = "completed"
    genres = "Drama, Fantastika, Sarguzasht, Jangari"
    poster_url = "https://image.tmdb.org/t/p/original/1XS1oqL89opfnbLl8WnZY1O1uJx.jpg"
    description = (
        "Etti zodagon oila afsonaviy Vesteros o'lkasini boshqarish uchun kurashadi. "
        "Uylar orasidagi ziddiyatlar, hokimiyat uchun urushlar, xiyonat va qadimiy tahdidlar — "
        "Temir Taxt uchun kurash butun qit'ani qamrab oladi."
    )
    director = "David Benioff, D.B. Weiss"
    cast = "Peter Dinklage, Lena Headey, Emilia Clarke, Kit Harington, Sophie Turner, Maisie Williams, Nikolaj Coster-Waldau"
    trailer_url = "https://www.youtube.com/watch?v=KPLWWIOCOOQ"

    logger.info(f"=== TAXTLAR O'YINI KO'CHIRISH BOSHLANMOQDA ===")
    logger.info(f"Eski manba: Chat {OLD_CHAT}, Topic {OLD_TOPIC_ID}")
    logger.info(f"Yangi manba superguruh: {TARGET_SUPERGROUP}")
    logger.info(f"Yangi saqlash kanali: {TARGET_STORAGE}")

    # 1. Topic yaratish yoki topish
    topic_title = f"🎬 {title} ({release_year})"
    topic_id = await create_or_find_topic(client, topic_title)
    logger.info(f"Topic tayyor! Topic ID: {topic_id}")
    await asyncio.sleep(1.5)

    # 2. Database Series va Source tekshirish/yaratish
    async with async_session_factory() as session:
        # Check source
        src_res = await session.execute(
            select(SourceModel).where(SourceModel.chat_id == TARGET_SUPERGROUP, SourceModel.topic_id == topic_id)
        )
        src = src_res.scalars().first()
        if not src:
            src = SourceModel(
                name=title,
                type="superguruh",
                chat_id=TARGET_SUPERGROUP,
                topic_id=topic_id
            )
            session.add(src)
            await session.flush()

        # Check series
        series_res = await session.execute(
            select(SeriesModel).where(SeriesModel.tmdb_id == tmdb_id)
        )
        series_obj = series_res.scalars().first()
        if not series_obj:
            series_obj = SeriesModel(
                title=title,
                description=description,
                status=status,
                publish_status="published",
                is_18_plus=False,
                imdb_rating=imdb_rating,
                release_year=release_year,
                tmdb_id=tmdb_id,
                poster_url="https://image.tmdb.org/t/p/w500/1XS1oqL89opfnbLl8WnZY1O1uJx.jpg",
                trailer_url=trailer_url,
                director=director,
                cast=cast,
                source_id=src.id,
                source_type="superguruh",
                custom_source_name="Kinochi @kinochi_mvp_bot"
            )
            session.add(series_obj)
            await session.flush()

            # Attach categories: Drama (3), Fantastika (6), Sarguzasht (8), Jangari (1)
            for cat_id in [1, 3, 6, 8]:
                try:
                    await session.execute(
                        insert(series_category_table).values(series_id=series_obj.id, category_id=cat_id)
                    )
                except Exception:
                    pass
            await session.commit()
            logger.info(f"Series bazaga qo'shildi! ID: {series_obj.id}")
        else:
            logger.info(f"Series bazada mavjud: ID {series_obj.id}")

        current_series_id = series_obj.id

    # 3. Post Banner if topic is fresh
    # Check if banner already sent
    has_banner = False
    async for m in client.iter_messages(TARGET_SUPERGROUP, reply_to=topic_id, limit=5):
        if m.photo or (m.text and title in m.text):
            has_banner = True
            break

    if not has_banner:
        logger.info("Banner poster jo'natilmoqda...")
        poster_bytes = await fetch_poster_bytes(poster_url)
        caption_banner = (
            f"🎬 <b>{html.escape(title)}</b> ({release_year})\n"
            f"🎭 <b>Janr:</b> {genres}\n"
            f"⭐ <b>IMDb:</b> {imdb_rating}/10\n"
            f"🇺🇿 <b>Tili:</b> O'zbek tilida\n"
            f"🎬 <b>Rejissyor:</b> {director}\n"
            f"👥 <b>Bosh rollarda:</b> {cast}\n\n"
            f"📖 <b>Tavsif:</b>\n{html.escape(description)}\n\n"
            f"🍿 @kinochi_mvp_bot orqali yuklandi."
        )

        topic_banner_msg = None
        if poster_bytes:
            f_st = io.BytesIO(poster_bytes)
            f_st.name = "poster.jpg"
            await client.send_file(TARGET_STORAGE, file=f_st, caption=caption_banner, parse_mode="html")
            await asyncio.sleep(1.5)

            f_sg = io.BytesIO(poster_bytes)
            f_sg.name = "poster.jpg"
            topic_banner_msg = await client.send_file(
                TARGET_SUPERGROUP,
                file=f_sg,
                caption=caption_banner,
                reply_to=topic_id,
                parse_mode="html"
            )
        else:
            await client.send_message(TARGET_STORAGE, message=caption_banner, parse_mode="html")
            topic_banner_msg = await client.send_message(
                TARGET_SUPERGROUP,
                message=caption_banner,
                reply_to=topic_id,
                parse_mode="html"
            )
        await asyncio.sleep(1.5)

        if topic_banner_msg:
            try:
                await client(UpdatePinnedMessageRequest(
                    peer=TARGET_SUPERGROUP,
                    id=topic_banner_msg.id,
                    silent=True
                ))
                logger.info(f"Banner topicga qadaldi (Msg ID: {topic_banner_msg.id})")
            except Exception as e:
                logger.warning(f"Bannerni qadashda ogohlantirish: {e}")
        await asyncio.sleep(1.5)

    # 4. Migrate Seasons and Episodes
    total_migrated = 0
    total_episodes_overall = sum(len(eps) for eps in GOT_SEASONS.values())
    current_index = 0

    for s_num in sorted(GOT_SEASONS.keys()):
        old_ep_ids = GOT_SEASONS[s_num]
        logger.info(f"\n>>> {s_num}-MAVSUM BOSHLANMOQDA: {len(old_ep_ids)} ta qism")

        current_season_id = None
        async with async_session_factory() as session:
            # Check or create SeasonModel
            season_res = await session.execute(
                select(SeasonModel).where(
                    SeasonModel.series_id == current_series_id,
                    SeasonModel.season_number == s_num
                )
            )
            season_obj = season_res.scalars().first()
            if not season_obj:
                season_obj = SeasonModel(
                    series_id=current_series_id,
                    season_number=s_num,
                    title=f"{s_num}-Mavsum",
                    status="completed",
                    poster_url="https://image.tmdb.org/t/p/w500/1XS1oqL89opfnbLl8WnZY1O1uJx.jpg",
                    episode_count=len(old_ep_ids)
                )
                session.add(season_obj)
                await session.flush()
                await session.commit()
                logger.info(f"{s_num}-Mavsum bazada yaratildi (ID: {season_obj.id})")
            else:
                logger.info(f"{s_num}-Mavsum bazada mavjud (ID: {season_obj.id})")

            current_season_id = season_obj.id

        for ep_idx, old_ep_msg_id in enumerate(old_ep_ids, start=1):
            current_index += 1
            display_code = f"S{s_num}-CH{ep_idx}"

            # Check if episode already exists in DB
            async with async_session_factory() as session:
                ep_chk = await session.execute(
                    select(EpisodeModel).where(
                        EpisodeModel.season_id == current_season_id,
                        EpisodeModel.episode_number == ep_idx
                    )
                )
                existing_ep = ep_chk.scalars().first()
                if existing_ep:
                    logger.info(f"[{current_index}/{total_episodes_overall}] Qism {display_code} allaqachon ko'chirilgan, o'tkazib yuborilmoqda.")
                    total_migrated += 1
                    continue

            # Fetch media from old chat
            ep_msg = None
            while True:
                try:
                    ep_msg = await client.get_messages(OLD_CHAT, ids=old_ep_msg_id)
                    break
                except FloodWaitError as fwe:
                    logger.warning(f"Flood wait {fwe.seconds}s on fetching message {old_ep_msg_id}")
                    await asyncio.sleep(fwe.seconds + 2)

            if not ep_msg or not (ep_msg.video or ep_msg.document):
                logger.warning(f"  [XATO] Msg ID {old_ep_msg_id} da media topilmadi!")
                continue

            ep_code = uuid.uuid4().hex[:8]
            caption_ep = (
                f"🎬 <b>{html.escape(title)}</b>\n"
                f"📺 <b>{s_num}-Mavsum, {ep_idx}-Qism</b>\n"
                f"🔑 <b>Qism kodi:</b> <code>{display_code}</code>\n"
                f"🇺🇿 <b>Tili:</b> O'zbek tilida\n\n"
                f"🍿 @kinochi_mvp_bot orqali yuklandi."
            )

            # Send to Storage Channel
            new_st_msg = None
            while True:
                try:
                    new_st_msg = await client.send_file(
                        TARGET_STORAGE,
                        file=ep_msg.media,
                        caption=caption_ep,
                        parse_mode="html"
                    )
                    break
                except FloodWaitError as fwe:
                    logger.warning(f"Flood wait {fwe.seconds}s on sending to storage")
                    await asyncio.sleep(fwe.seconds + 2)

            await asyncio.sleep(1.0)

            # Send to Supergroup Topic
            new_sg_msg = None
            while True:
                try:
                    new_sg_msg = await client.send_file(
                        TARGET_SUPERGROUP,
                        file=ep_msg.media,
                        caption=caption_ep,
                        reply_to=topic_id,
                        parse_mode="html"
                    )
                    break
                except FloodWaitError as fwe:
                    logger.warning(f"Flood wait {fwe.seconds}s on sending to topic")
                    await asyncio.sleep(fwe.seconds + 2)

            await asyncio.sleep(0.8)

            # Send Confirmation index text to Topic
            while True:
                try:
                    await client.send_message(
                        TARGET_SUPERGROUP,
                        message=f"✅ **{ep_idx}-qism** saqlandi va indekslandi. Kod: `{display_code}`",
                        reply_to=topic_id
                    )
                    break
                except FloodWaitError as fwe:
                    logger.warning(f"Flood wait {fwe.seconds}s on sending index confirmation")
                    await asyncio.sleep(fwe.seconds + 2)

            await asyncio.sleep(0.6)

            # Save in Database
            async with async_session_factory() as session:
                ep_obj = EpisodeModel(
                    season_id=current_season_id,
                    episode_number=ep_idx,
                    code=ep_code,
                    display_code=display_code,
                    title=f"{ep_idx}-qism",
                    source_message_id=new_st_msg.id
                )
                session.add(ep_obj)
                await session.flush()

                trans_obj = EpisodeTranslationModel(
                    episode_id=ep_obj.id,
                    language="O'zbekcha",
                    storage_channel_message_id=new_st_msg.id
                )
                session.add(trans_obj)
                await session.commit()

            total_migrated += 1
            logger.info(f"[{current_index}/{total_episodes_overall}] [OK] {display_code} muvaffaqiyatli saqlandi! (Storage Msg ID: {new_st_msg.id})")

    # Invalidate Cache
    try:
        from app.core.cache import delete_cache_pattern
        await delete_cache_pattern("series*")
        await delete_cache_pattern("search*")
        await delete_cache_pattern("catalog*")
        logger.info("Keshlar tozalandi.")
    except Exception as e:
        logger.warning(f"Keshni tozalashda xatolik: {e}")

    logger.info(f"\n==================================================")
    logger.info(f"MUVAFFAQIYAT! Barcha {total_migrated}/{total_episodes_overall} qismlar ko'chirildi va bazaga yozildi!")
    logger.info(f"==================================================")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
