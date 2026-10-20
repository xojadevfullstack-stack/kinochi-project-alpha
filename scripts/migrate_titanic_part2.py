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
from app.core.cache import delete_cache_pattern

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("titanic_p2")

TARGET_SUPERGROUP = int(settings.AUTO_TOPIC_CHAT_ID)
TARGET_STORAGE = int(settings.STORAGE_CHANNEL_ID)
SOURCE_CHANNEL = -1003941035700
SOURCE_MSG_ID = 940

MOVIE_DATA = {
    "title": "Titanik (2-qism)",
    "original_title": "Titanic (Part 2)",
    "release_year": 1997,
    "tmdb_id": None,  # None to prevent conflict with Part 1 (597)
    "imdb_rating": 7.9,
    "poster_url": "https://image.tmdb.org/t/p/w500/r3sYKBtoNHPyS9vkaA8dJyh8grG.jpg",
    "description": "Jek va Rouz fojiali 'Titanik' kemasidagi sevgisini saqlab qolish uchun aysbergga urilgan ulkan kemaning cho'kib borayotgan sovuq suvlarida omon qolish uchun kurashadi.",
    "genres": "Drama, Romantika",
    "runtime": 85
}

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

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    await client.get_dialogs()

    title = MOVIE_DATA["title"]
    logger.info(f"=== {title} ko'chirish boshlandi ===")

    # 1. Manba videosini olish
    old_msg = await client.get_messages(SOURCE_CHANNEL, ids=SOURCE_MSG_ID)
    if not old_msg or not old_msg.media:
        logger.error(f"Xatolik: {SOURCE_CHANNEL} dagi msg {SOURCE_MSG_ID} topilmadi!")
        await client.disconnect()
        return

    # 2. Topic ochish
    topic_id = await create_or_get_topic(client, title)
    logger.info(f"Topic ochildi! Topic ID: {topic_id}")
    await asyncio.sleep(2.0)

    # 3. Topic Banner yuborish
    poster_bytes = await fetch_poster_bytes(MOVIE_DATA["poster_url"])
    caption_banner = (
        f"🎬 <b>{html.escape(title)}</b> ({MOVIE_DATA['release_year']})\n"
        f"🎭 <b>Janr:</b> {MOVIE_DATA['genres']}\n"
        f"⭐ <b>IMDb:</b> {MOVIE_DATA['imdb_rating']}/10\n"
        f"🇺🇿 <b>Tili:</b> O'zbek tilida (2-bo'lak / davomi)\n\n"
        f"📖 <b>Tavsif:</b>\n{html.escape(MOVIE_DATA['description'])}\n\n"
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

    # 4. Videoni yuborish
    movie_code = uuid.uuid4().hex[:8]
    caption_video = (
        f"🎬 <b>{html.escape(title)}</b> ({MOVIE_DATA['release_year']})\n"
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
            top_msg = await client.send_file(TARGET_SUPERGROUP, file=old_msg.media, caption=caption_video, reply_to=topic_id, parse_mode="html")
            break
        except FloodWaitError as fwe:
            await asyncio.sleep(fwe.seconds + 2)

    # 5. DB ga saqlash
    async with async_session_factory() as session:
        movie_obj = MovieModel(
            title=title,
            original_title=MOVIE_DATA["original_title"],
            description=MOVIE_DATA["description"],
            imdb_rating=MOVIE_DATA["imdb_rating"],
            release_year=MOVIE_DATA["release_year"],
            runtime=MOVIE_DATA["runtime"],
            genres=MOVIE_DATA["genres"],
            poster_url=MOVIE_DATA["poster_url"],
            code=movie_code,
            publish_status="published",
            is_18_plus=False,
            source_chat_id=TARGET_SUPERGROUP,
            source_topic_id=topic_id,
            source_type="superguruh",
            custom_source_name="Kinochi @kinochi_mvp_bot"
        )
        session.add(movie_obj)
        await session.flush()

        trans_obj = MovieTranslationModel(
            movie_id=movie_obj.id,
            language="O'zbekcha",
            storage_channel_message_id=st_msg.id if st_msg else None
        )
        session.add(trans_obj)
        await session.commit()
        logger.info(f"DB ga muvaffaqiyatli saqlandi! Movie ID: {movie_obj.id}")

    await client.disconnect()
    logger.info("=== TITANIK 2-QISM MIGRATSIYASI YAKUNLANDI! ===")

if __name__ == "__main__":
    asyncio.run(main())
