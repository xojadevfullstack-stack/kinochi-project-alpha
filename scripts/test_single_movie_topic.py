import asyncio
import os
import sys
import random
import secrets
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.core.config import settings
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.translation import MovieTranslationModel
from sqlalchemy import select
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.tl.functions.messages import CreateForumTopicRequest

TARGET_SUPERGROUP = int(settings.AUTO_TOPIC_CHAT_ID) # -1003847632555
TARGET_STORAGE = int(settings.STORAGE_CHANNEL_ID)    # -1003762157591
OLD_STORAGE = -1003926001543

async def test():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    m_title = "Shrek 1"
    m_orig = "Shrek"
    m_year = 2001
    m_tmdb = 808
    m_imdb = 7.9
    m_poster = "https://image.tmdb.org/t/p/w500/dyhaB19AIC4PkYQ2Y7YbpCNIIOx.jpg"
    old_msg_id = 14488

    # 1. Create Topic
    peer = await client.get_input_entity(TARGET_SUPERGROUP)
    topic_title = f"{m_title} ({m_year})"
    res = await client(CreateForumTopicRequest(
        peer=peer,
        title=topic_title[:128],
        random_id=random.randint(1, 2**31 - 1)
    ))
    topic_id = None
    for u in getattr(res, 'updates', []):
        if hasattr(u, 'message') and hasattr(u.message, 'id'):
            topic_id = u.message.id
            break
        elif hasattr(u, 'id'):
            topic_id = u.id
            break

    print(f"Created topic '{topic_title}' with Topic ID: {topic_id}")

    # 2. Get Old Video Message
    old_msg = await client.get_messages(OLD_STORAGE, ids=old_msg_id)
    if not old_msg or not (old_msg.video or old_msg.document):
        print(f"Old video msg {old_msg_id} not found!")
        return

    # 3. Update or Insert Movie in DB with topic_id FIRST
    async with async_session_factory() as session:
        res_m = await session.execute(select(MovieModel).where(MovieModel.tmdb_id == m_tmdb))
        movie = res_m.scalar_one_or_none()
        m_code = movie.code if movie and movie.code else secrets.token_hex(4)

        if movie:
            movie.source_chat_id = TARGET_SUPERGROUP
            movie.source_topic_id = topic_id
            movie.source_type = "superguruh"
            movie.custom_source_name = "Kinochi @kinochi_mvp_bot"
            movie.poster_url = m_poster
            movie.title = m_title
            movie.release_year = m_year
        else:
            movie = MovieModel(
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
            session.add(movie)

        await session.commit()
        print(f"Committed movie to DB: ID {movie.id}, code={m_code}, topic_id={topic_id}")

    # 4. Send Video to Topic
    caption = (
        f"🍿 <b>{m_title}</b> ({m_year})\n\n"
        f"🔑 <b>Film kodi:</b> <code>{m_code}</code>\n"
        f"⭐ <b>IMDb:</b> {m_imdb}\n\n"
        f"🤖 Bot orqali tomosha qiling: @kinochi_mvp_bot"
    )
    sent_msg = await client.send_file(
        entity=TARGET_SUPERGROUP,
        file=old_msg.media,
        caption=caption,
        reply_to=topic_id,
        parse_mode="html"
    )
    print(f"Sent video to topic {topic_id}! Msg ID: {sent_msg.id}")

    # 5. Wait a few seconds to let auto_index trigger and observe
    print("Waiting 6 seconds for auto_index...")
    await asyncio.sleep(6.0)

    # Check replies in topic
    replies = await client.get_messages(TARGET_SUPERGROUP, reply_to=sent_msg.id, limit=5)
    for r in replies:
        print(f"Bot reply: {r.message}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(test())
