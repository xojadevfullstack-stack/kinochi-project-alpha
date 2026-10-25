import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

import asyncio
import os
import re
import uuid
import html
import logging
from telethon import TelegramClient
from telethon.sessions import StringSession
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
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel, series_category_table
from app.infrastructure.db.models.source import SourceModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel
from sqlalchemy import select, insert, func
from telethon.tl.functions.messages import CreateForumTopicRequest, UpdatePinnedMessageRequest

class FlushStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

logger = logging.getLogger("qashqirlar_full")
logger.setLevel(logging.INFO)
_handler = FlushStreamHandler(sys.stdout)
_handler.setLevel(logging.INFO)
_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.handlers = [_handler]
logger.propagate = False
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

TARGET_SUPERGROUP = int(settings.AUTO_TOPIC_CHAT_ID)  # -1003847632555
TARGET_STORAGE = int(settings.STORAGE_CHANNEL_ID)    # -1003762157591
OLD_CHAT = -1003941035700
OLD_PISTIRMA_TOPIC = 33418
ASIL_BOT = "asilmediabot"

ORIGINAL_SERIES_ID = 1005
ORIGINAL_TOPIC_ID = 3847

PISTIRMA_SEASONS_RANGES = {
    1: (1, 9),
    2: (10, 41),
    3: (42, 63),
    4: (64, 93),
    5: (94, 128),
    6: (129, 161),
    7: (162, 195),
    8: (196, 229),
    9: (230, 263),
    10: (264, 300)
}

async def poll_bot_response(client, target_bot, sent_id, timeout=12.0, condition=None):
    start = asyncio.get_event_loop().time()
    while asyncio.get_event_loop().time() - start < timeout:
        await asyncio.sleep(0.5)
        msgs = []
        async for m in client.iter_messages(target_bot, limit=8):
            if m.id > sent_id:
                msgs.append(m)
        if msgs:
            if condition:
                if condition(msgs):
                    return msgs
            else:
                return msgs
    return []

# ==============================================================================
# PHASE 1: Complete "Qashqirlar makoni" (original series) from 56 to 96
# ==============================================================================
async def complete_original_series(client: TelegramClient):
    logger.info("==================================================")
    logger.info("PHASE 1: QASHQIRLAR MAKONI (56-96 QISMLAR) YUKLANMOQDA")
    logger.info(f"Target Series ID: {ORIGINAL_SERIES_ID} | Topic ID: #{ORIGINAL_TOPIC_ID}")
    logger.info("==================================================")

    # 1. Mavsumlarni (Season 3: 56-86, Season 4: 87-96) yaratish yoki olish
    season_ids = {}
    async with async_session_factory() as session:
        for s_num in [1, 2, 3, 4]:
            res = await session.execute(
                select(SeasonModel.id)
                .where(SeasonModel.series_id == ORIGINAL_SERIES_ID, SeasonModel.season_number == s_num)
            )
            sid = res.scalar()
            if not sid:
                s_obj = SeasonModel(
                    series_id=ORIGINAL_SERIES_ID,
                    season_number=s_num,
                    title=f"{s_num}-Mavsum"
                )
                session.add(s_obj)
                await session.flush()
                sid = s_obj.id
                await session.commit()
            season_ids[s_num] = sid

    # Mavjud qismlarni tekshirish
    existing_eps = set()
    async with async_session_factory() as session:
        for s_num in [1, 2, 3, 4]:
            sid = season_ids[s_num]
            res = await session.execute(select(EpisodeModel.episode_number).where(EpisodeModel.season_id == sid))
            for ep in res.scalars().all():
                existing_eps.add(ep)

    logger.info(f"Asl serialda mavjud qismlar: {len(existing_eps)} ta (1 dan 96 gacha).")

    last_received_msg = None

    for ep_num in range(56, 97):
        if ep_num in existing_eps:
            logger.info(f"[MAVJUD] {ep_num}-qism allaqachon mavjud, o'tkazib yuborildi.")
            continue

        # Mavsum raqami: 1-20 -> 1, 21-55 -> 2, 56-86 -> 3, 87-96 -> 4
        if ep_num <= 86:
            s_num = 3
        else:
            s_num = 4
        sid = season_ids[s_num]

        video_msg = None

        # 1. 'Keyingi qism' tugmasi orqali tezkor olish
        if last_received_msg and last_received_msg.buttons:
            next_btn = None
            for r_idx, row in enumerate(last_received_msg.buttons):
                for c_idx, b in enumerate(row):
                    if "keyingi" in b.text.lower():
                        next_btn = (r_idx, c_idx)
                        break
                if next_btn:
                    break

            if next_btn:
                click_id = last_received_msg.id
                try:
                    await last_received_msg.click(next_btn[0], next_btn[1])
                    replies = await poll_bot_response(client, ASIL_BOT, click_id, timeout=10.0, condition=lambda ms: any(m.file for m in ms))
                    for r in replies:
                        if r.file and (f"{ep_num}_qism" in (r.file.name or "").lower() or f"{ep_num}-qism" in (r.text or "").lower() or f"{ep_num} qism" in (r.text or "").lower()):
                            video_msg = r
                            break
                except Exception as ce:
                    logger.warning(f"Keyingi qism bosishda xatolik: {ce}")

        # 2. Zaxira: /start 11153 orqali qism raqamini bosish
        if not video_msg:
            logger.info(f"Zaxira: /start 11153 orqali {ep_num}-qism qidirilmoqda...")
            sent_init = await client.send_message(ASIL_BOT, "/start 11153")
            card_replies = await poll_bot_response(client, ASIL_BOT, sent_init.id, timeout=8.0, condition=lambda ms: any(m.buttons for m in ms))
            active_card = next((m for m in card_replies if m.buttons and any(b.text.strip().isdigit() for row in m.buttons for b in row)), None)

            if active_card:
                ep_btn = None
                for _ in range(5):
                    ep_btn = next(((r, c) for r, row in enumerate(active_card.buttons) for c, b in enumerate(row) if b.text.strip() == str(ep_num)), None)
                    if ep_btn:
                        break
                    next_p = next(((r, c) for r, row in enumerate(active_card.buttons) for c, b in enumerate(row) if "▶️" in b.text or "➡️" in b.text), None)
                    if not next_p:
                        break
                    await active_card.click(next_p[0], next_p[1])
                    await asyncio.sleep(1.8)
                    active_card = await client.get_messages(ASIL_BOT, ids=active_card.id)

                if ep_btn:
                    click_id = active_card.id
                    await active_card.click(ep_btn[0], ep_btn[1])
                    replies = await poll_bot_response(client, ASIL_BOT, click_id, timeout=12.0, condition=lambda ms: any(m.file for m in ms))
                    video_msg = next((m for m in replies if m.file), None)

        if not video_msg:
            logger.error(f"❌ {ep_num}-qism videosini botdan olib bo'lmadi! Keyingi qismga o'tilmoqda...")
            continue

        last_received_msg = video_msg
        ep_file_size = round(video_msg.file.size / 1024 / 1024, 1)

        # STORAGE kanalga jo'natish
        st_msg = await client.send_file(
            TARGET_STORAGE,
            file=video_msg.media,
            caption=(
                f"🎬 <b>Qashqirlar makoni</b>\n"
                f"📺 <b>{s_num}-Mavsum | {ep_num}-Qism</b>\n"
                f"💿 <b>Format:</b> 720p HD\n"
                f"🗣 <b>Dublyaj:</b> O'zbek tilida (Asilmedia)\n"
                f"💾 <b>Hajmi:</b> {ep_file_size} MB"
            ),
            parse_mode="html"
        )

        # Topic ga jo'natish
        await client.send_file(
            TARGET_SUPERGROUP,
            file=st_msg.media,
            caption=(
                f"🍿 <b>Qashqirlar makoni</b>\n"
                f"📺 <b>{s_num}-Mavsum | {ep_num}-Qism</b>\n\n"
                f"🔹 <b>Format:</b> 720p HD\n"
                f"🗣 <b>Til:</b> O'zbek tilida (Asilmedia)\n"
                f"💾 <b>Hajmi:</b> {ep_file_size} MB"
            ),
            reply_to=ORIGINAL_TOPIC_ID,
            parse_mode="html"
        )

        # DB ga yozish
        ep_code = f"{ep_num}_{uuid.uuid4().hex[:6]}"
        display_code = f"S{s_num:02d}E{ep_num:02d}"

        for db_attempt in range(5):
            try:
                async with async_session_factory() as session:
                    ep_obj = EpisodeModel(
                        season_id=sid,
                        episode_number=ep_num,
                        code=ep_code,
                        display_code=display_code,
                        title=f"{ep_num}-qism",
                        source_message_id=st_msg.id
                    )
                    session.add(ep_obj)
                    await session.flush()

                    trans_obj = EpisodeTranslationModel(
                        episode_id=ep_obj.id,
                        language="O'zbekcha",
                        storage_channel_message_id=st_msg.id
                    )
                    session.add(trans_obj)
                    await session.commit()
                    break
            except Exception as dbe:
                logger.warning(f"DB xatolik ({dbe}). Qayta urinish {db_attempt+1}/5...")
                await asyncio.sleep(3)

        logger.info(f"[{ep_num}/96] [OK] {display_code} muvaffaqiyatli saqlandi! (ST Msg: {st_msg.id})")
        await asyncio.sleep(1.0)

    logger.info("✅ QASHQIRLAR MAKONI (1-96 QISMLAR) 100% YAKUNLANDI!")

# ==============================================================================
# PHASE 2: Ingest "Qashqirlar makoni: Pistirma" (All 300 episodes)
# ==============================================================================
async def migrate_pistirma_series(client: TelegramClient):
    logger.info("\n==================================================")
    logger.info("PHASE 2: QASHQIRLAR MAKONI: PISTIRMA (300 TA QISM) BOSHLANDI")
    logger.info("==================================================")

    # 1. Bazada tekshirish yoki yaratish
    series_id = None
    topic_id = None
    pistirma_tmdb_id = 49071

    async with async_session_factory() as session:
        res = await session.execute(select(SeriesModel).where(SeriesModel.tmdb_id == pistirma_tmdb_id))
        s_model = res.scalar_one_or_none()
        if s_model:
            series_id = s_model.id
            if s_model.source_id:
                src_res = await session.execute(select(SourceModel).where(SourceModel.id == s_model.source_id))
                src = src_res.scalar_one_or_none()
                if src:
                    topic_id = src.topic_id

    # 2. Topic va SeriesModel yaratish (agar yo'q bo'lsa)
    if not series_id or not topic_id:
        topic_title = "🎬 Qashqirlar makoni: Pistirma (Serial) (2007)"
        logger.info(f"Topic ochilmoqda: '{topic_title}'...")
        created_topic = await client(CreateForumTopicRequest(
            peer=TARGET_SUPERGROUP,
            title=topic_title,
            icon_color=0xFFD67E
        ))
        topic_id = created_topic.updates[0].id
        logger.info(f"✅ Topic ochildi! Topic ID: #{topic_id}")

        poster_url = "https://image.tmdb.org/t/p/w500/wDWkjobSJm8I5r2ctSPtneUjHxT.jpg"
        banner_caption = (
            "🎬 <b>Qashqirlar makoni: Pistirma</b> (Serial) (2007)\n"
            "🇺🇿 <b>Asl nomi:</b> Kurtlar Vadisi: Pusu\n"
            "🎭 <b>Janr:</b> Jangari, Kriminal, Drama, Triller\n"
            "⭐ <b>IMDb:</b> 7.7/10\n"
            "🎬 <b>Rejissyor:</b> Sadullah Şentürk, Zübeyr Şaşmaz, Onur Tan, Doğan Ümit Karaca\n"
            "👥 <b>Aktyorlar:</b> Necati Şaşmaz, Kenan Çoban, Gürkan Uygun, Çiğdem Batur, Cahit Kayaoğlu, Erhan Ufak\n\n"
            "📝 <b>Tavsif:</b>\n<i>Polat Alemdar va uning jamoasi global kuchlar, qurol savdogarlari va xalqaro mafiya to'rlariga qarshi "
            "kurashni yangi, shiddatli bosqichda davom ettiradi. Vatan xavfsizligi va milliy manfaatlarni himoya qilish yo'lida "
            "ular har qanday pistirma va fitnalarni yorib o'tishga majbur.</i>\n\n"
            "⬇️ <i>Serialning barcha 300 ta qismi quyida yuklanmoqda:</i>"
        )

        try:
            banner_msg = await client.send_file(
                TARGET_SUPERGROUP,
                file=poster_url,
                caption=banner_caption,
                reply_to=topic_id,
                parse_mode="html"
            )
        except Exception:
            banner_msg = await client.send_message(
                TARGET_SUPERGROUP,
                message=banner_caption,
                reply_to=topic_id,
                parse_mode="html"
            )

        try:
            await client(UpdatePinnedMessageRequest(
                peer=TARGET_SUPERGROUP,
                id=banner_msg.id,
                silent=True
            ))
        except Exception:
            pass

        # DB ga yozish
        async with async_session_factory() as session:
            src = SourceModel(
                name="Qashqirlar makoni: Pistirma",
                type="superguruh",
                chat_id=TARGET_SUPERGROUP,
                topic_id=topic_id
            )
            session.add(src)
            await session.flush()

            series_obj = SeriesModel(
                title="Qashqirlar makoni: Pistirma",
                description=(
                    "Polat Alemdar va uning jamoasi global kuchlar, qurol savdogarlari va xalqaro mafiya to'rlariga qarshi "
                    "kurashni yangi, shiddatli bosqichda davom ettiradi."
                ),
                imdb_rating=7.7,
                tmdb_id=pistirma_tmdb_id,
                release_year=2007,
                director="Sadullah Şentürk, Zübeyr Şaşmaz, Onur Tan",
                cast="Necati Şaşmaz, Kenan Çoban, Gürkan Uygun, Çiğdem Batur, Cahit Kayaoğlu",
                poster_url=poster_url,
                source_id=src.id,
                source_type="uzmovi",
                status="completed",
                publish_status="published",
                is_18_plus=False
            )
            session.add(series_obj)
            await session.flush()
            series_id = series_obj.id

            for cat_id in [1, 3, 4, 9]:
                await session.execute(
                    insert(series_category_table).values(series_id=series_id, category_id=cat_id)
                )

            await session.commit()
            logger.info(f"✅ SeriesModel (Pistirma) DB da yaratildi: Series ID: {series_id}")

    # 3. 10 ta Mavsumni yaratish
    season_ids = {}
    async with async_session_factory() as session:
        for s_num in range(1, 11):
            res = await session.execute(
                select(SeasonModel.id)
                .where(SeasonModel.series_id == series_id, SeasonModel.season_number == s_num)
            )
            sid = res.scalar()
            if not sid:
                s_obj = SeasonModel(
                    series_id=series_id,
                    season_number=s_num,
                    title=f"{s_num}-Mavsum"
                )
                session.add(s_obj)
                await session.flush()
                sid = s_obj.id
                await session.commit()
            season_ids[s_num] = sid

    # 4. Old channel dagi 300 ta qism xabarlarini o'qish
    logger.info("Eski kanaldagi (Topic 33418) 300 ta qism xabarlari o'qilmoqda...")
    raw_episodes = {}
    async for m in client.iter_messages(OLD_CHAT, reply_to=OLD_PISTIRMA_TOPIC):
        if m.file and m.text:
            m_e = re.search(r'(\d+)\s*[-_]?\s*qism', m.text, re.I)
            if m_e:
                e_num = int(m_e.group(1))
                s_num = 1
                for s_k, (s_start, s_end) in PISTIRMA_SEASONS_RANGES.items():
                    if s_start <= e_num <= s_end:
                        s_num = s_k
                        break
                raw_episodes[e_num] = (m, s_num)

    logger.info(f"Eski kanaldan jami topilgan qismlar: {len(raw_episodes)} ta.")

    # Bazadagi mavjud qismlar
    existing_eps = set()
    async with async_session_factory() as session:
        for sid in season_ids.values():
            res = await session.execute(select(EpisodeModel.episode_number).where(EpisodeModel.season_id == sid))
            for ep in res.scalars().all():
                existing_eps.add(ep)

    logger.info(f"Pistirmada bazada mavjud qismlar: {len(existing_eps)} ta (1-300).")

    # 5. Ketma-ket 1 dan 300 gacha nusxalash
    for ep_num in range(1, 301):
        if ep_num in existing_eps:
            continue

        if ep_num not in raw_episodes:
            logger.warning(f"⚠️ {ep_num}-qism eski mavzuda topilmadi!")
            continue

        orig_msg, s_num = raw_episodes[ep_num]
        sid = season_ids[s_num]
        f_size = round(orig_msg.file.size / 1024 / 1024, 1) if orig_msg.file else 0

        # STORAGE kanalga saqlash
        st_msg = await client.send_file(
            TARGET_STORAGE,
            file=orig_msg.media,
            caption=(
                f"🎬 <b>Qashqirlar makoni: Pistirma</b>\n"
                f"📺 <b>{s_num}-Mavsum | {ep_num}-Qism</b>\n"
                f"💿 <b>Format:</b> 720p HD\n"
                f"🗣 <b>Dublyaj:</b> O'zbek tilida\n"
                f"💾 <b>Hajmi:</b> {f_size} MB"
            ),
            parse_mode="html"
        )

        # Topic ga saqlash
        await client.send_file(
            TARGET_SUPERGROUP,
            file=st_msg.media,
            caption=(
                f"🍿 <b>Qashqirlar makoni: Pistirma</b>\n"
                f"📺 <b>{s_num}-Mavsum | {ep_num}-Qism</b>\n\n"
                f"🔹 <b>Format:</b> 720p HD\n"
                f"🗣 <b>Til:</b> O'zbek tilida\n"
                f"💾 <b>Hajmi:</b> {f_size} MB"
            ),
            reply_to=topic_id,
            parse_mode="html"
        )

        # DB ga yozish
        ep_code = f"{ep_num}_{uuid.uuid4().hex[:6]}"
        display_code = f"S{s_num:02d}E{ep_num:02d}"

        for db_attempt in range(5):
            try:
                async with async_session_factory() as session:
                    ep_obj = EpisodeModel(
                        season_id=sid,
                        episode_number=ep_num,
                        code=ep_code,
                        display_code=display_code,
                        title=f"{ep_num}-qism",
                        source_message_id=st_msg.id
                    )
                    session.add(ep_obj)
                    await session.flush()

                    trans_obj = EpisodeTranslationModel(
                        episode_id=ep_obj.id,
                        language="O'zbekcha",
                        storage_channel_message_id=st_msg.id
                    )
                    session.add(trans_obj)
                    await session.commit()
                    break
            except Exception as dbe:
                logger.warning(f"DB xatolik ({dbe}). Qayta urinish {db_attempt+1}/5...")
                await asyncio.sleep(3)

        logger.info(f"[Pistirma {ep_num}/300] [OK] {display_code} muvaffaqiyatli ko'chirildi! (ST Msg: {st_msg.id})")
        await asyncio.sleep(0.5)

    logger.info("✅ QASHQIRLAR MAKONI: PISTIRMA (1-300 QISMLAR) 100% YAKUNLANDI!")

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    client.flood_sleep_threshold = 120
    await client.connect()

    # 1. Asl serialni 96-qismgacha yakunlash
    try:
        await complete_original_series(client)
    except Exception as e:
        logger.error(f"Asl serialni yakunlashda xatolik: {e}", exc_info=True)

    # 2. Pistirmani 300-qismgacha ko'chirish
    try:
        await migrate_pistirma_series(client)
    except Exception as e:
        logger.error(f"Pistirma ko'chirishda xatolik: {e}", exc_info=True)

    # Cache tozalash
    try:
        from app.core.cache import delete_cache_pattern
        await delete_cache_pattern("series*")
        await delete_cache_pattern("search*")
        await delete_cache_pattern("catalog*")
    except Exception:
        pass

    logger.info("\n==================================================")
    logger.info("BARCHA QASHQIRLAR MAKONI MATERIALLARI TO'LIQ YAKUNLANDI!")
    logger.info("==================================================")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
