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
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.translation import MovieTranslationModel

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("interstellar_migration")

TARGET_SUPERGROUP = int(settings.AUTO_TOPIC_CHAT_ID)
TARGET_STORAGE = int(settings.STORAGE_CHANNEL_ID)
SOURCE_CHANNEL = -1003941035700

INTERSTELLAR_PARTS = [
    {
        "title": "Interstellar (1-qism)",
        "original_title": "Interstellar (Part 1)",
        "release_year": 2014,
        "tmdb_id": None,
        "imdb_rating": 8.7,
        "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
        "description": "Insoniyat Yer yuzida halokat yoqasida turgan bir paytda, bir guruh tadqiqotchilar va astronavtlar insoniyat uchun yangi yashash makonini topish maqsadida koinotdagi qurt teshigi orqali xavfli sayohatga otlanadilar.",
        "genres": "Ilmiy-fantastika, Drama, Sarguzasht",
        "runtime": 85,
        "source_msg_id": 922
    },
    {
        "title": "Interstellar (2-qism)",
        "original_title": "Interstellar (Part 2)",
        "release_year": 2014,
        "tmdb_id": None,
        "imdb_rating": 8.7,
        "poster_url": "https://image.tmdb.org/t/p/w500/gEU2QniE6E77NI6lCU6MxlNBvIx.jpg",
        "description": "Kuper va Brend noma'lum sayyoralarda vaqt va fazo qonuniyatlariga qarshi kurashadilar. Qora tuynuk ichiga kirish va insoniyatni qutqarish uchun oxirgi hal qiluvchi qadam qo'yiladi.",
        "genres": "Ilmiy-fantastika, Drama, Sarguzasht",
        "runtime": 84,
        "source_msg_id": 924
    }
]

async def fetch_poster_bytes(url: str) -> bytes | None:
    try:
        async with httpx.AsyncClient(timeout=15) as hclient:
            res = await hclient.get(url)
            if res.status_code == 200:
                return res.content
    except Exception as e:
        logger.warning(f"Poster yuklab olishda xatolik ({url}): {e}")
    return None

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

async def migrate_single_part(client: TelegramClient, m_data: dict):
    title = m_data["title"]
    logger.info(f"=== Boshlandi: {title} ===")

    old_msg = await client.get_messages(SOURCE_CHANNEL, ids=m_data["source_msg_id"])
    if not old_msg or not old_msg.media:
        logger.error(f"Xato: Msg {m_data['source_msg_id']} topilmadi!")
        return

    # 1. Topic ochish
    topic_id = await create_or_get_topic(client, title)
    logger.info(f"Topic ochildi! Topic ID: {topic_id}")
    await asyncio.sleep(2.0)

    # 2. Topic Banner yuborish va qadash
    poster_bytes = await fetch_poster_bytes(m_data["poster_url"])
    caption_banner = (
        f"🎬 <b>{html.escape(title)}</b> ({m_data['release_year']})\n"
        f"🎭 <b>Janr:</b> {m_data['genres']}\n"
        f"⭐ <b>IMDb:</b> {m_data['imdb_rating']}/10\n"
        f"🇺🇿 <b>Tili:</b> O'zbek tilida\n\n"
        f"📖 <b>Tavsif:</b>\n{html.escape(m_data['description'])}\n\n"
        f"🍿 @kinochi_mvp_bot orqali yuklandi."
    )

    banner_msg = None
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
                banner_msg = await client.send_file(
                    TARGET_SUPERGROUP,
                    file=f_sg,
                    caption=caption_banner,
                    reply_to=topic_id,
                    parse_mode="html"
                )
                break
            except FloodWaitError as fwe:
                await asyncio.sleep(fwe.seconds + 2)

    await asyncio.sleep(1.5)
    if banner_msg:
        try:
            from telethon.tl.functions.messages import UpdatePinnedMessageRequest
            await client(UpdatePinnedMessageRequest(
                peer=TARGET_SUPERGROUP,
                id=banner_msg.id,
                silent=True
            ))
            logger.info("Banner topicga qadaldi")
        except Exception as e:
            logger.warning(f"Bannerni qadashda ogohlantirish: {e}")

    await asyncio.sleep(1.5)

    # 3. Videoni yuborish
    movie_code = uuid.uuid4().hex[:8]
    caption_video = (
        f"🎬 <b>{html.escape(title)}</b> ({m_data['release_year']})\n"
        f"🔢 <b>Kodi:</b> <code>{movie_code}</code>\n"
        f"🇺🇿 <b>Tili:</b> O'zbek tilida\n\n"
        f"🍿 @kinochi_mvp_bot orqali yuklandi."
    )

    st_msg = None
    while True:
        try:
            st_msg = await client.send_file(TARGET_STORAGE, file=old_msg.media, caption=caption_video, parse_mode="html")
            break
        except FloodWaitError as fwe:
            await asyncio.sleep(fwe.seconds + 2)

    await asyncio.sleep(1.0)

    top_msg = None
    while True:
        try:
            top_msg = await client.send_file(
                TARGET_SUPERGROUP,
                file=st_msg.media,
                caption=caption_video,
                reply_to=topic_id,
                parse_mode="html"
            )
            break
        except FloodWaitError as fwe:
            await asyncio.sleep(fwe.seconds + 2)

    storage_msg_id = st_msg.id
    logger.info(f"Video saqlandi: storage_msg_id={storage_msg_id}, topic_msg_id={top_msg.id}")

    # 4. PostgreSQL ga yozish
    async with async_session_factory() as session:
        movie = MovieModel(
            title=title,
            original_title=m_data["original_title"],
            description=m_data["description"],
            imdb_rating=m_data["imdb_rating"],
            tmdb_id=m_data["tmdb_id"],
            release_year=m_data["release_year"],
            runtime=m_data["runtime"],
            poster_url=m_data["poster_url"],
            code=movie_code,
            genres=m_data["genres"],
            source_chat_id=TARGET_SUPERGROUP,
            source_topic_id=topic_id,
            source_type="superguruh",
            custom_source_name="Kinochi @kinochi_mvp_bot",
            publish_status="published",
            is_18_plus=False
        )
        session.add(movie)
        await session.flush()

        trans = MovieTranslationModel(
            movie_id=movie.id,
            language="O'zbekcha",
            storage_channel_message_id=storage_msg_id
        )
        session.add(trans)
        await session.commit()
        logger.info(f"DB ga muvaffaqiyatli saqlandi! Movie ID: {movie.id}")

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    logger.info("Telegram client ulandi.")

    for m_data in INTERSTELLAR_PARTS:
        await migrate_single_part(client, m_data)
        logger.info("10 soniya kutish...")
        await asyncio.sleep(10.0)

    await client.disconnect()
    logger.info("Interstellar split qismlarini yuklash to'liq yakunlandi!")

if __name__ == "__main__":
    asyncio.run(main())
