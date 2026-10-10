import os
import sys
import re
import asyncio
from dotenv import load_dotenv

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, "bot", ".env"))
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from telethon.tl.functions.messages import EditForumTopicRequest
from scraper.telethon_moderator_pipeline import create_telethon_client
from scraper.config import AUTO_TOPIC_CHAT_ID
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.series import SeriesModel
from app.infrastructure.db.models.source import SourceModel
from app.core.cache import delete_cache_pattern

SERIES_DATA = [
    {
        "series_id": 501,
        "topic_id": 15086,
        "clean_title": "📺 Kaiju 8",
        "name": "Kaiju 8"
    },
    {
        "series_id": 503,
        "topic_id": 15120,
        "clean_title": "📺 Qahramon x",
        "name": "Qahramon x"
    },
    {
        "series_id": 505,
        "topic_id": 15265,
        "clean_title": "📺 Iblislar qotili",
        "name": "Iblislar qotili"
    },
    {
        "series_id": 507,
        "topic_id": 15303,
        "clean_title": "📺 Gleipnir",
        "name": "Gleipnir"
    }
]

async def update_database():
    print("--- 1. Bazadagi manbalarni yaratish va bog'lash ---")
    chat_id_int = int(AUTO_TOPIC_CHAT_ID)

    async with async_session_factory() as session:
        for item in SERIES_DATA:
            sid = item["series_id"]
            topic_id = item["topic_id"]
            name = item["name"]

            series = await session.get(SeriesModel, sid)
            if not series:
                print(f"Serial #{sid} topilmadi!")
                continue

            # Manba mavjudligini tekshirish
            source = None
            if series.source_id:
                source = await session.get(SourceModel, series.source_id)

            if not source:
                source = SourceModel(
                    name=name,
                    type="superguruh",
                    chat_id=chat_id_int,
                    topic_id=topic_id
                )
                session.add(source)
                await session.flush()
                series.source_id = source.id
                print(f"✅ Serial #{sid} ({name}) uchun yangi SourceModel #{source.id} (topic_id={topic_id}) yaratildi va bog'landi.")
            else:
                source.topic_id = topic_id
                source.chat_id = chat_id_int
                print(f"ℹ️ Serial #{sid} ({name}) manbasi #{source.id} mavjud, topic_id={topic_id} yangilandi.")

        await session.commit()

    try:
        await delete_cache_pattern("cache:series:*")
        print("✅ Seriallar keshi tozalandi.")
    except Exception as e:
        print(f"Kesh tozalashda xatolik: {e}")

async def send_confirmations_and_rename_topics():
    print("\n--- 2. Telegram topic nomlarini to'g'rilash va tasdiq xabarlarini yuborish ---")
    client = create_telethon_client()
    await client.connect()
    if not await client.is_user_authorized():
        print("Xatolik: Telethon avtorizatsiyadan o'tmagan!")
        return

    entity = await client.get_entity(AUTO_TOPIC_CHAT_ID)

    # Serial qismlarini bazadan olish
    series_episodes_map = {}
    async with async_session_factory() as session:
        for item in SERIES_DATA:
            sid = item["series_id"]
            s = await session.get(SeriesModel, sid)
            eps_by_num = {}
            if s and s.seasons:
                for ep in s.seasons[0].episodes:
                    eps_by_num[ep.episode_number] = ep.display_code
            series_episodes_map[sid] = eps_by_num

    for item in SERIES_DATA:
        sid = item["series_id"]
        topic_id = item["topic_id"]
        clean_title = item["clean_title"]
        name = item["name"]
        episodes_map = series_episodes_map.get(sid, {})

        print(f"\n▶ Topic {topic_id} ({name}, Series #{sid}) tekshirilmoqda...")

        # 1. Topic sarlavhasini tahrirlash (ortiqcha () ni olib tashlash)
        try:
            await client(EditForumTopicRequest(
                peer=entity,
                topic_id=topic_id,
                title=clean_title
            ))
            print(f"  ✏️ Topic nomi yangilandi: '{clean_title}'")
        except Exception as ren_err:
            print(f"  ⚠️ Topic nomini yangilashda ogohlantirish: {ren_err}")

        # 2. Topicdagi xabarlarni o'qish
        msgs = await client.get_messages(entity, reply_to=topic_id, limit=60)
        video_messages = []
        confirmed_ep_reply_ids = set()

        for m in reversed(msgs):
            # Qaysi xabarlar allaqachon tasdiqlanganini tekshirish
            if m.text and "saqlandi va indekslandi" in m.text:
                if m.reply_to_msg_id:
                    confirmed_ep_reply_ids.add(m.reply_to_msg_id)

            if m.video or (m.document and (m.document.mime_type or "").startswith("video/")):
                caption = m.text or ""
                # Captiondan qism raqamini topish (masalan '1-Qism' yoki '1-qism')
                m_ep = re.search(r'(\d+)[\s\-_]*[qQ]ism', caption)
                ep_num = int(m_ep.group(1)) if m_ep else None
                video_messages.append((m.id, ep_num))

        print(f"  Topilgan video xabarlar: {len(video_messages)} ta, oldin tasdiqlangan: {len(confirmed_ep_reply_ids)} ta")

        # 3. Har bir video xabarga tasdiq javobi yuborish
        for v_msg_id, ep_num in video_messages:
            if not ep_num:
                continue

            if v_msg_id in confirmed_ep_reply_ids:
                print(f"  ⏩ {ep_num}-qism (msg #{v_msg_id}) allaqachon tasdiqlangan, o'tkazib yuborildi.")
                continue

            display_code = episodes_map.get(ep_num, f"S1-CH{ep_num}")
            confirm_text = (
                f"✅ <b>{ep_num}-qism</b> saqlandi va indekslandi.\n"
                f"🔑 Qism kodi: <code>{display_code}</code>\n"
                f"📺 Serial kodi: <code>s_{sid}</code>"
            )

            try:
                await client.send_message(
                    entity,
                    message=confirm_text,
                    reply_to=v_msg_id,
                    parse_mode="html"
                )
                print(f"  ✅ {ep_num}-qism (msg #{v_msg_id}, kod: {display_code}) uchun tasdiq xabari yuborildi.")
                await asyncio.sleep(1.0)
            except Exception as send_err:
                print(f"  ❌ {ep_num}-qism uchun tasdiq yuborishda xatolik: {send_err}")
                await asyncio.sleep(2.0)

    await client.disconnect()
    print("\n🎉 Barcha amallar muvaffaqiyatli yakunlandi!")

async def main():
    await update_database()
    await send_confirmations_and_rename_topics()

if __name__ == "__main__":
    asyncio.run(main())
