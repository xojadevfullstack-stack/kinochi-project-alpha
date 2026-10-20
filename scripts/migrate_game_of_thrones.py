import asyncio
import os
import sys
import random
import uuid
import html
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
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
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.models.source import SourceModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("got_migration")

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
    status = "completed"
    genres = "Fentezi, Drama, Sarguzasht, Jangari"

    logger.info(f"=== Boshlanmoqda: {title} ===")

    # 1. Fetch Banner Message
    banner_msg_id = 439
    banner_msg = await client.get_messages(OLD_STORAGE, ids=banner_msg_id)
    description = (banner_msg.message or title).strip() if banner_msg else title
    lines = description.split('\n')
    desc_clean = "\n".join([l for l in lines if not l.startswith('🎬') and not l.startswith('🍿')]).strip()
    if not desc_clean:
        desc_clean = description

    # 2. Create Topic in new Supergroup
    topic_title = f"{title}"
    logger.info(f"Yangi superguruhda Topic ochilmoqda: '{topic_title}'...")
    topic_id = await create_or_get_topic(client, topic_title)
    logger.info(f"Topic ochildi! Topic ID: {topic_id}")
    await asyncio.sleep(1.5)

    # 3. Post Banner to Topic
    caption_banner = (
        f"🎬 <b>{html.escape(title)}</b> ({release_year})\n"
        f"🎭 <b>Janr:</b> {genres}\n"
        f"⭐ <b>IMDb:</b> {imdb_rating}/10\n"
        f"🇺🇿 <b>Tili:</b> O'zbek tilida\n\n"
        f"📖 <b>Tavsif:</b>\n{html.escape(desc_clean[:700])}\n\n"
        f"🍿 @kinochi_mvp_bot orqali yuklandi."
    )
    if banner_msg and banner_msg.media:
        await client.send_file(
            TARGET_SUPERGROUP,
            file=banner_msg.media,
            caption=caption_banner,
            reply_to=topic_id,
            parse_mode="html"
        )
    else:
        await client.send_message(
            TARGET_SUPERGROUP,
            message=caption_banner,
            reply_to=topic_id,
            parse_mode="html"
        )
    await asyncio.sleep(1.5)

    # Exact seasons mapping for all 73 episodes
    got_seasons = {
        1: [457, 458, 459, 460, 461, 462, 463, 464, 465, 466],
        2: [468, 469, 470, 471, 472, 473, 474, 475, 476, 477],
        3: [489, 490, 491, 492, 493, 494, 495, 496, 497, 498],
        4: [500, 501, 502, 503, 504, 505, 506, 507, 508, 509],
        5: [511, 512, 513, 514, 515, 516, 517, 518, 519, 520],
        6: [522, 523, 524, 525, 526, 527, 528, 529, 530, 531],
        7: [533, 534, 535, 536, 537, 538, 539],
        8: [541, 542, 543, 544, 545, 546]
    }

    # 4. Database Setup
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
            description=desc_clean,
            status=status,
            publish_status="published",
            is_18_plus=False,
            imdb_rating=imdb_rating,
            release_year=release_year,
            source_id=src.id,
            source_type="superguruh",
            custom_source_name=f"Kinochi @kinochi_mvp_bot"
        )
        session.add(series_obj)
        await session.flush()

        total_migrated = 0

        for s_num in sorted(got_seasons.keys()):
            old_msg_ids = got_seasons[s_num]
            logger.info(f"{title} -> {s_num}-Mavsum: {len(old_msg_ids)} ta qism ko'chirilmoqda...")

            season_obj = SeasonModel(
                series_id=series_obj.id,
                season_number=s_num,
                title=f"{s_num}-Mavsum",
                status="completed",
                episode_count=len(old_msg_ids)
            )
            session.add(season_obj)
            await session.flush()

            for ep_idx, old_ep_msg_id in enumerate(old_msg_ids, start=1):
                ep_msg = await client.get_messages(OLD_STORAGE, ids=old_ep_msg_id)
                if not ep_msg or not ep_msg.video:
                    logger.warning(f"  Msg ID {old_ep_msg_id} da video topilmadi!")
                    continue

                display_code = f"S{s_num}-CH{ep_idx}"
                ep_code = uuid.uuid4().hex[:8]

                caption_ep = (
                    f"🎬 <b>{html.escape(title)}</b>\n"
                    f"📺 <b>{s_num}-Mavsum, {ep_idx}-Qism</b>\n"
                    f"🔑 <b>Qism kodi:</b> <code>{display_code}</code>\n"
                    f"🇺🇿 <b>Tili:</b> O'zbek tilida\n\n"
                    f"🍿 @kinochi_mvp_bot orqali yuklandi."
                )

                # Send to Storage Channel
                new_st_msg = await client.send_file(
                    TARGET_STORAGE,
                    file=ep_msg.media,
                    caption=caption_ep,
                    parse_mode="html"
                )
                await asyncio.sleep(1.0)

                # Send to Supergroup Topic
                await client.send_file(
                    TARGET_SUPERGROUP,
                    file=ep_msg.media,
                    caption=caption_ep,
                    reply_to=topic_id,
                    parse_mode="html"
                )
                await asyncio.sleep(1.2)

                # Save Episode
                ep_obj = EpisodeModel(
                    season_id=season_obj.id,
                    episode_number=ep_idx,
                    code=ep_code,
                    display_code=display_code,
                    title=f"{ep_idx}-qism",
                    source_message_id=new_st_msg.id
                )
                session.add(ep_obj)
                await session.flush()

                # Save Translation
                trans_obj = EpisodeTranslationModel(
                    episode_id=ep_obj.id,
                    language="O'zbekcha",
                    storage_channel_message_id=new_st_msg.id
                )
                session.add(trans_obj)

                total_migrated += 1
                logger.info(f"  [OK] GOT {display_code} (ST Msg ID: {new_st_msg.id})")

        await session.commit()
        logger.info(f"=== MUVAFFAQISh: '{title}' barcha {total_migrated} ta qismi muvaffaqiyatli ko'chirildi! ===")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
