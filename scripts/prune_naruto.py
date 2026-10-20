import asyncio
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(BASE_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from dotenv import load_dotenv
load_dotenv(os.path.join(BASE_DIR, ".env.local"))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, ".env"))

from app.core.config import settings
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel
from sqlalchemy import select, delete
from telethon import TelegramClient
from telethon.sessions import StringSession

TARGET_SUPERGROUP = int(settings.AUTO_TOPIC_CHAT_ID)
TARGET_STORAGE = int(settings.STORAGE_CHANNEL_ID)

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")
    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()
    await client.get_dialogs()

    async with async_session_factory() as session:
        res = await session.execute(select(SeriesModel).where(SeriesModel.title.ilike('%naruto%')))
        naruto = res.scalars().first()
        if not naruto:
            print("Naruto topilmadi!")
            return

        res_season = await session.execute(select(SeasonModel).where(SeasonModel.series_id == naruto.id))
        season = res_season.scalars().first()

        res_eps = await session.execute(
            select(EpisodeModel).where(
                EpisodeModel.season_id == season.id,
                EpisodeModel.episode_number > 25
            ).order_by(EpisodeModel.episode_number.asc())
        )
        eps_to_delete = res_eps.scalars().all()
        print(f"O'chirilishi kerak bo'lgan Naruto qismlari: {len(eps_to_delete)} ta (26 dan 111 gacha)")

        sg_msg_ids = []
        st_msg_ids = []
        ep_ids = []

        for ep in eps_to_delete:
            ep_ids.append(ep.id)
            if ep.source_message_id:
                sg_msg_ids.append(ep.source_message_id)

            res_tr = await session.execute(
                select(EpisodeTranslationModel).where(EpisodeTranslationModel.episode_id == ep.id)
            )
            tr = res_tr.scalars().first()
            if tr and tr.storage_channel_message_id:
                st_msg_ids.append(tr.storage_channel_message_id)

        print(f"Superguruhdan o'chiriladigan xabarlar: {len(sg_msg_ids)} ta")
        print(f"Storagedan o'chiriladigan xabarlar: {len(st_msg_ids)} ta")

        # Telegramdan o'chirish (guruhlab 50 tadan)
        for i in range(0, len(sg_msg_ids), 50):
            chunk = sg_msg_ids[i:i+50]
            try:
                await client.delete_messages(TARGET_SUPERGROUP, chunk)
                print(f"Superguruhdan {len(chunk)} ta xabar o'chirildi")
            except Exception as e:
                print(f"Superguruhdan o'chirishda xatolik: {e}")
            await asyncio.sleep(1.0)

        for i in range(0, len(st_msg_ids), 50):
            chunk = st_msg_ids[i:i+50]
            try:
                await client.delete_messages(TARGET_STORAGE, chunk)
                print(f"Storagedan {len(chunk)} ta xabar o'chirildi")
            except Exception as e:
                print(f"Storagedan o'chirishda xatolik: {e}")
            await asyncio.sleep(1.0)

        # DB dan o'chirish
        await session.execute(
            delete(EpisodeTranslationModel).where(EpisodeTranslationModel.episode_id.in_(ep_ids))
        )
        await session.execute(
            delete(EpisodeModel).where(EpisodeModel.id.in_(ep_ids))
        )

        season.episode_count = 25
        await session.commit()
        print("Bazada Naruto 1-mavsum qismlari 25 taga qisqartirildi va qolganlari tozalandi!")

    await client.disconnect()
    print("Muvaffaqiyatli yakunlandi!")

if __name__ == "__main__":
    asyncio.run(main())
