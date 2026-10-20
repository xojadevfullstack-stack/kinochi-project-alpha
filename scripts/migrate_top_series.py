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
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
logger = logging.getLogger("series_migration")

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

async def migrate_series(
    client: TelegramClient,
    title: str,
    original_title: str,
    tmdb_id: int,
    poster_url: str,
    description: str,
    seasons_data: dict,  # {season_num: [old_msg_id_1, old_msg_id_2, ...]}
    imdb_rating: float = 8.5,
    release_year: int = 2024,
    status: str = "completed",
    genres: str = "Drama, Kriminal",
):
    safe_title = title.encode('ascii', errors='replace').decode('ascii')
    logger.info(f"=== Boshlanmoqda: {safe_title} ===")

    # 1. Fetch Poster Bytes
    poster_bytes = await fetch_poster_bytes(poster_url)
    
    # 2. Create Topic in new Supergroup
    topic_title = f"{title}"
    logger.info(f"Yangi superguruhda Topic ochilmoqda: '{safe_title}'...")
    topic_id = await create_or_get_topic(client, topic_title)
    logger.info(f"Topic ochildi! Topic ID: {topic_id}")
    await asyncio.sleep(1.5)

    # 3. Post Banner to Storage Channel & Topic
    caption_banner = (
        f"🎬 <b>{html.escape(title)}</b> ({release_year})\n"
        f"🎭 <b>Janr:</b> {genres}\n"
        f"⭐ <b>IMDb:</b> {imdb_rating}/10\n"
        f"🇺🇿 <b>Tili:</b> O'zbek tilida\n\n"
        f"📖 <b>Tavsif:</b>\n{html.escape(description[:700])}\n\n"
        f"🍿 @kinochi_mvp_bot orqali yuklandi."
    )

    # Send to Storage Channel
    if poster_bytes:
        f_st = io.BytesIO(poster_bytes)
        f_st.name = "poster.jpg"
        await client.send_file(
            TARGET_STORAGE,
            file=f_st,
            caption=caption_banner,
            parse_mode="html"
        )
        await asyncio.sleep(1.2)

        # Send to Supergroup Topic
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
        topic_banner_msg = await client.send_message(TARGET_SUPERGROUP, message=caption_banner, reply_to=topic_id, parse_mode="html")
    
    await asyncio.sleep(1.5)

    # Pin Banner in Topic
    if topic_banner_msg:
        try:
            from telethon.tl.functions.messages import UpdatePinnedMessageRequest
            await client(UpdatePinnedMessageRequest(
                peer=TARGET_SUPERGROUP,
                id=topic_banner_msg.id,
                silent=True
            ))
            logger.info(f"Banner muvaffaqiyatli qadaldi (Msg ID: {topic_banner_msg.id})")
        except Exception as e:
            logger.warning(f"Bannerni qadashda ogohlantirish: {e}")

    await asyncio.sleep(1.5)

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
            custom_source_name=f"Kinochi @kinochi_mvp_bot"
        )
        session.add(series_obj)
        await session.flush()

        total_migrated = 0

        for s_num in sorted(seasons_data.keys()):
            old_msg_ids = seasons_data[s_num]
            logger.info(f"{safe_title} -> {s_num}-Mavsum: {len(old_msg_ids)} ta qism ko'chirilmoqda...")

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
                ep_msg = await client.get_messages(OLD_STORAGE, ids=old_ep_msg_id)
                if not ep_msg or not (ep_msg.video or ep_msg.document):
                    logger.warning(f"  Msg ID {old_ep_msg_id} da media topilmadi!")
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
                logger.info(f"  [OK] {safe_title} {display_code} (ST Msg ID: {new_st_msg.id})")

        await session.commit()
        logger.info(f"=== MUVAFFAQISh: '{safe_title}' barcha {total_migrated} ta qismi ko'chirildi! ===")

SERIES_TO_MIGRATE = [
    {
        "title": "Oʻtkir soyabonlar",
        "original_title": "Peaky Blinders",
        "tmdb_id": 60574,
        "poster_url": "https://image.tmdb.org/t/p/w500/vUUqzWa2LnHIVqkaKVlVGkVcZIW.jpg",
        "description": "1919-yilgi Birmingem. Tomas Shelbi va uning shafqatsiz jinoiy guruhi — Peaky Blinders shahar ustidan nazoratni qo'lga oladi. Ingliz kriminal klassikasi.",
        "imdb_rating": 8.8,
        "release_year": 2013,
        "status": "completed",
        "genres": "Kriminal, Drama, Tarixiy",
        "seasons_data": {
            1: [753, 754, 755, 756, 757, 758],
            2: [760, 761, 762, 763, 764, 765],
            3: [767, 768, 769, 770, 771, 772],
            4: [780, 781, 782, 783, 784, 785],
            5: [787, 788, 789, 790, 791, 792],
            6: [794, 795, 796, 797, 798, 799],
        }
    },
    {
        "title": "Kalmar oʻyini",
        "original_title": "Squid Game",
        "tmdb_id": 93405,
        "poster_url": "https://image.tmdb.org/t/p/w500/dDlGgwXbmsA5p84p862p3yR03f.jpg",
        "description": "Og'ir moliyaviy ahvoldagi 456 nafar kishi ulkan pul mukofoti (45.6 milliard von) uchun bolalar o'yinlariga asoslangan sirli va halokatli omon qolish o'yinida qatnashadi.",
        "imdb_rating": 8.0,
        "release_year": 2021,
        "status": "ongoing",
        "genres": "Triller, Drama, Omon qolish",
        "seasons_data": {
            1: [2091, 2092, 2093, 2094, 2095, 2096, 2097, 2098, 2099],
            2: [2101, 2102, 2103, 2104, 2105, 2106, 2107],
            3: [2109, 2110, 2111, 2112, 2113, 2114],
        }
    },
    {
        "title": "Gʻaroyib ishlar",
        "original_title": "Stranger Things",
        "tmdb_id": 66732,
        "poster_url": "https://image.tmdb.org/t/p/w500/49WJfeN0moxb9IPfGn8AIqMGskD.jpg",
        "description": "1980-yillar, Indiana shtatidagi Xokins shaharchasi. Kichik bolakay Uillning sirli g'oyib bo'lishi ortidan maxfiy hukumat tajribalari, g'ayritabiiy kuchlar va telekinezga ega qizaloq — O'n birinchi fosh bo'ladi.",
        "imdb_rating": 8.7,
        "release_year": 2016,
        "status": "ongoing",
        "genres": "Ilmiy fantastika, Dahshat, Drama",
        "seasons_data": {
            1: [14508, 14510, 14512, 14514, 14516, 14518, 14520, 14522, 14524, 14526]
        }
    }
]

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    for item in SERIES_TO_MIGRATE:
        try:
            await migrate_series(
                client=client,
                title=item["title"],
                original_title=item["original_title"],
                tmdb_id=item["tmdb_id"],
                poster_url=item["poster_url"],
                description=item["description"],
                seasons_data=item["seasons_data"],
                imdb_rating=item["imdb_rating"],
                release_year=item["release_year"],
                status=item["status"],
                genres=item["genres"]
            )
            await asyncio.sleep(3.0)
        except Exception as e:
            logger.error(f"Xatolik {item['title']} ni ko'chirishda: {e}", exc_info=True)

    await client.disconnect()
    logger.info("=== BARCHA 1-GURUH SERIALLARI KO'CHIRILDI! ===")

if __name__ == "__main__":
    asyncio.run(main())
