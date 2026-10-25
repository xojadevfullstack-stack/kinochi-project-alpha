import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace", line_buffering=True)

import asyncio
import os
import random
import uuid
import html
import re
import logging
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
from app.infrastructure.db.models.movie import MovieModel, movie_category_table
from app.infrastructure.db.models.translation import MovieTranslationModel, EpisodeTranslationModel
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel, series_category_table
from app.infrastructure.db.models.source import SourceModel
from sqlalchemy import select, insert, func
from telethon.tl.functions.messages import CreateForumTopicRequest, UpdatePinnedMessageRequest

class FlushStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

logger = logging.getLogger("qashqirlar_migrator")
logger.setLevel(logging.INFO)
_handler = FlushStreamHandler(sys.stdout)
_handler.setLevel(logging.INFO)
_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
logger.handlers = [_handler]
logger.propagate = False
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

TARGET_SUPERGROUP = int(settings.AUTO_TOPIC_CHAT_ID)  # -1003847632555
TARGET_STORAGE = int(settings.STORAGE_CHANNEL_ID)    # -1003762157591
ASIL_BOT = "asilmediabot"

MOVIES_CONFIG = [
    {
        "asil_id": 12090,
        "title": "Qashqirlar makoni: Iroq",
        "original_title": "Kurtlar Vadisi: Irak",
        "release_year": 2006,
        "tmdb_id": 14197,
        "imdb_rating": 6.0,
        "genres": "Jangari, Triller, Urush",
        "category_ids": [1, 4, 16],
        "director": "Serdar Akar",
        "cast": "Necati Şaşmaz, Billy Zane, Ghassan Massoud, Bergüzar Korel, Gürkan Uygun",
        "description": (
            "Shimoliy Iroqda turk maxsus kuchlariga qarshi uyushtirilgan shafqatsiz amaliyotdan so'ng, "
            "qasos va adolat izlab Polat Alemdar va uning sodiq safdoshlari Iroqqa yo'l oladi."
        )
    },
    {
        "asil_id": 12403,
        "title": "Qashqirlar makoni: Falastin",
        "original_title": "Kurtlar Vadisi: Filistin",
        "release_year": 2011,
        "tmdb_id": 54159,
        "imdb_rating": 6.0,
        "genres": "Jangari, Drama, Triller, Urush",
        "category_ids": [1, 3, 4, 16],
        "director": "Zübeyr Şaşmaz",
        "cast": "Necati Şaşmaz, Nur Fettahoğlu, Erdal Beşikçioğlu, Gürkan Uygun, Kenan Çoban",
        "description": (
            "G'azo sohillariga yo'l olgan insonparvarlik yordami kemasiga qilingan qonli hujumdan so'ng, "
            "Polat Alemdar va uning guruhi Falastin xalqiga qarshi jinoyatlarga sababchi bo'lgan Isroil qo'mondoni "
            "Moshe Ben Eliezerning iziga tushadi."
        )
    },
    {
        "asil_id": 14932,
        "title": "Qashqirlar makoni: Vatan",
        "original_title": "Kurtlar Vadisi: Vatan",
        "release_year": 2017,
        "tmdb_id": 472093,
        "imdb_rating": 5.5,
        "genres": "Jangari, Drama, Triller, Urush",
        "category_ids": [1, 3, 4, 16],
        "director": "Serdar Akar",
        "cast": "Necati Şaşmaz, Sinem Uslu, Cahit Kayaoğlu, Erhan Ufak, Nezih Işıtan",
        "description": (
            "2016-yil 15-iyuldagi davlat to'ntarishiga urinish paytida Polat Alemdar va uning jamoasi "
            "Turkiya chegarasida mamlakatni parchalashni rejalashtirgan xoinlar va tashqi dushmanlarga qarshi "
            "shiddatli jangga kirishadi."
        )
    }
]

SERIES_CONFIG = {
    "asil_id": 11153,
    "title": "Qashqirlar makoni",
    "original_title": "Kurtlar Vadisi",
    "release_year": 2003,
    "tmdb_id": 3122,
    "imdb_rating": 8.2,
    "genres": "Jangari, Jinoyat, Drama, Klassika",
    "category_ids": [1, 3, 9, 29],
    "director": "Osman Sınav, Serdar Akar, Mustafa Şevki Doğan",
    "cast": "Necati Şaşmaz, Özgü Namal, Selçuk Yöntem, Oktay Kaynarca, Gürkan Uygun, Kenan Çoban",
    "description": (
        "Ali Candan maxfiy xizmat topshirig'i bilan yuzini o'zgartirib, Polat Alemdar ismi ostida "
        "qudratli mafiya tarmog'iga kirib boradi va davlat xavfsizligiga tahdid solayotgan mafiya kengashini "
        "ichkaridan yo'q qilishga kirishadi."
    ),
    "allowed_seasons": {
        1: (1, 20),   # 1-mavsum: 1-20 qismlar
        2: (21, 55),  # 2-mavsum: 21-55 qismlar
    }
}

def generate_movie_code():
    alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    return "".join(random.choice(alphabet) for _ in range(6))

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

async def migrate_single_movie(client: TelegramClient, m_cfg: dict):
    title = m_cfg["title"]
    asil_id = m_cfg["asil_id"]
    year = m_cfg["release_year"]
    logger.info(f"\n{'='*55}\n[KINO] '{title}' ({year}) ko'chirilmoqda...\n{'='*55}")

    # 1. Bazada bormi?
    async with async_session_factory() as session:
        res = await session.execute(
            select(MovieModel.id, MovieModel.code, MovieModel.source_topic_id)
            .where(MovieModel.tmdb_id == m_cfg["tmdb_id"])
        )
        existing = res.first()
        if existing:
            logger.info(f"Kino bazada allaqachon mavjud: ID={existing[0]}, Kod={existing[1]}, Topic={existing[2]}. O'tkazib yuborildi.")
            return

    # 2. Asilmediabot dan kartani olish
    logger.info(f"@{ASIL_BOT} botiga '/start {asil_id}' so'rovi yuborilmoqda...")
    sent = await client.send_message(ASIL_BOT, f"/start {asil_id}")
    replies = await poll_bot_response(client, ASIL_BOT, sent.id, timeout=10.0, condition=lambda ms: any(m.buttons for m in ms))
    
    card_msg = None
    for r in replies:
        if r.buttons and any(any(q in b.text for q in ["1080", "720", "480"]) for row in r.buttons for b in row):
            card_msg = r
            break

    if not card_msg:
        logger.error(f"@{ASIL_BOT} dan '{title}' kino kartasi olinmadi!")
        return

    # Poster sifatida card_msg dagi rasmni olamiz
    poster_media = card_msg.media

    # 3. Sifat tanlash (720p yoki 1080p)
    quality_btn = None
    for row_idx, row in enumerate(card_msg.buttons):
        for col_idx, b in enumerate(row):
            if "720" in b.text:
                quality_btn = (row_idx, col_idx, b.text)
                break
        if quality_btn:
            break
    if not quality_btn:
        for row_idx, row in enumerate(card_msg.buttons):
            for col_idx, b in enumerate(row):
                if "1080" in b.text or "480" in b.text:
                    quality_btn = (row_idx, col_idx, b.text)
                    break
            if quality_btn:
                break

    if not quality_btn:
        logger.error("Sifat tugmasi topilmadi!")
        return

    logger.info(f"Sifat tanlanmoqda: '{quality_btn[2]}'...")
    click_id = card_msg.id
    await card_msg.click(quality_btn[0], quality_btn[1])

    # Videoni kutish
    video_msgs = await poll_bot_response(client, ASIL_BOT, click_id, timeout=18.0, condition=lambda ms: any(m.file for m in ms))
    video_msg = next((m for m in video_msgs if m.file), None)
    if not video_msg:
        logger.error(f"@{ASIL_BOT} dan '{title}' video fayli qabul qilinmadi!")
        return

    f_size = round(video_msg.file.size / 1024 / 1024, 1)
    f_name = video_msg.file.name or f"{title}.mp4"
    logger.info(f"✅ Video muvaffaqiyatli qabul qilindi: {f_name} ({f_size} MB)")

    # 4. Superguruhda Forum Topic yaratish
    topic_title = f"🎬 {title} ({year})"
    logger.info(f"Topic ochilmoqda: '{topic_title}'...")
    created_topic = await client(CreateForumTopicRequest(
        peer=TARGET_SUPERGROUP,
        title=topic_title,
        icon_color=0x6FB9F0
    ))
    topic_id = created_topic.updates[0].id
    logger.info(f"✅ Topic ochildi! Topic ID: {topic_id}")

    # 5. Boshlang'ich banner xabari
    banner_caption = (
        f"🎬 <b>{html.escape(title)}</b> ({year})\n"
        f"🇺🇿 <b>Asl nomi:</b> {html.escape(m_cfg['original_title'])}\n"
        f"🎭 <b>Janr:</b> {html.escape(m_cfg['genres'])}\n"
        f"⭐ <b>IMDb:</b> {m_cfg['imdb_rating']}/10\n"
        f"🎬 <b>Rejissyor:</b> {html.escape(m_cfg['director'])}\n"
        f"👥 <b>Aktyorlar:</b> {html.escape(m_cfg['cast'])}\n\n"
        f"📝 <b>Tavsif:</b>\n<i>{html.escape(m_cfg['description'])}</i>\n\n"
        f"⬇️ <i>Film videosi pastda yuklangan:</i>"
    )

    if poster_media:
        banner_msg = await client.send_file(
            TARGET_SUPERGROUP,
            file=poster_media,
            caption=banner_caption,
            reply_to=topic_id,
            parse_mode="html"
        )
    else:
        banner_msg = await client.send_message(
            TARGET_SUPERGROUP,
            message=banner_caption,
            reply_to=topic_id,
            parse_mode="html"
        )

    # Pin banner
    try:
        await client(UpdatePinnedMessageRequest(
            peer=TARGET_SUPERGROUP,
            id=banner_msg.id,
            silent=True
        ))
    except Exception as pe:
        logger.warning(f"Bannerni qadashda ogohlantirish: {pe}")

    # 6. Videoni STORAGE kanaliga saqlash
    logger.info(f"Video STORAGE kanaliga ({TARGET_STORAGE}) nusxalanmoqda...")
    st_msg = await client.send_file(
        TARGET_STORAGE,
        file=video_msg.media,
        caption=(
            f"🎬 <b>{html.escape(title)}</b> ({year})\n"
            f"💿 <b>Sifat:</b> 720p HD\n"
            f"🗣 <b>Dublyaj:</b> O'zbek tilida (Asilmedia)\n"
            f"💾 <b>Hajmi:</b> {f_size} MB"
        ),
        parse_mode="html"
    )

    # 7. Videoni Forum Topic ga jo'natish
    logger.info(f"Video Topic #{topic_id} ga jo'natilmoqda...")
    await client.send_file(
        TARGET_SUPERGROUP,
        file=st_msg.media,
        caption=(
            f"🍿 <b>{html.escape(title)}</b> ({year})\n\n"
            f"🔹 <b>Sifat:</b> 720p HD\n"
            f"🗣 <b>Til:</b> O'zbek tilida (Asilmedia)\n"
            f"💾 <b>Hajm:</b> {f_size} MB"
        ),
        reply_to=topic_id,
        parse_mode="html"
    )

    # 8. Bazaga saqlash (MovieModel + MovieTranslationModel + Categories)
    movie_code = generate_movie_code()
    async with async_session_factory() as session:
        movie_obj = MovieModel(
            title=title,
            original_title=m_cfg["original_title"],
            description=m_cfg["description"],
            imdb_rating=m_cfg["imdb_rating"],
            tmdb_rating=m_cfg["imdb_rating"],
            tmdb_id=m_cfg["tmdb_id"],
            genres=m_cfg["genres"],
            cast=m_cfg["cast"],
            director=m_cfg["director"],
            release_year=year,
            code=movie_code,
            publish_status="published",
            is_18_plus=False,
            source_chat_id=TARGET_SUPERGROUP,
            source_topic_id=topic_id,
            source_type="asilmedia"
        )
        session.add(movie_obj)
        await session.flush()

        # Translation
        trans_obj = MovieTranslationModel(
            movie_id=movie_obj.id,
            language="O'zbekcha",
            storage_channel_message_id=st_msg.id
        )
        session.add(trans_obj)

        # Categories
        for cat_id in m_cfg["category_ids"]:
            await session.execute(
                insert(movie_category_table).values(movie_id=movie_obj.id, category_id=cat_id)
            )

        await session.commit()
        movie_id = movie_obj.id

    # 9. Topic ga indeks tasdiq xabari
    confirm_text = (
        f"✅ <b>Kino videosi saqlandi va indekslandi.</b>\n"
        f"🔑 Kod: <code>{movie_code}</code>\n"
        f"🌐 Websaytda onlayn tomosha qilishga tayyor!"
    )
    await client.send_message(TARGET_SUPERGROUP, confirm_text, reply_to=topic_id, parse_mode="html")

    logger.info(f"✅ [OK] '{title}' muvaffaqiyatli saqlandi! Movie ID: {movie_id}, Kod: {movie_code}, Topic: {topic_id}")

async def migrate_qashqirlar_series(client: TelegramClient, s_cfg: dict):
    title = s_cfg["title"]
    asil_id = s_cfg["asil_id"]
    year = s_cfg["release_year"]
    allowed_seasons = s_cfg["allowed_seasons"]
    logger.info(f"\n{'='*55}\n[SERIAL] '{title}' ({year}) ko'chirilmoqda...\n{'='*55}")

    # 1. Bazada tekshirish yoki yaratish
    series_id = None
    topic_id = None
    current_season_ids = {}

    async with async_session_factory() as session:
        res = await session.execute(select(SeriesModel).where(SeriesModel.tmdb_id == s_cfg["tmdb_id"]))
        s_model = res.scalar_one_or_none()
        if s_model:
            series_id = s_model.id
            if s_model.source_id:
                src_res = await session.execute(select(SourceModel).where(SourceModel.id == s_model.source_id))
                src = src_res.scalar_one_or_none()
                if src:
                    topic_id = src.topic_id

    # 2. Agar mavjud bo'lmasa, Topic va Series yaratish
    if not series_id or not topic_id:
        topic_title = f"🎬 {title} (Serial) ({year})"
        logger.info(f"Topic ochilmoqda: '{topic_title}'...")
        created_topic = await client(CreateForumTopicRequest(
            peer=TARGET_SUPERGROUP,
            title=topic_title,
            icon_color=0x53DF83
        ))
        topic_id = created_topic.updates[0].id
        logger.info(f"✅ Topic ochildi! Topic ID: {topic_id}")

        # Banner xabarini yuborish
        # Asilmediadan poster olish uchun /start 11153 yuboramiz
        sent_c = await client.send_message(ASIL_BOT, f"/start {asil_id}")
        c_replies = await poll_bot_response(client, ASIL_BOT, sent_c.id, timeout=8.0, condition=lambda ms: any(m.media for m in ms))
        card_media = next((m.media for m in c_replies if m.media), None)

        banner_caption = (
            f"🎬 <b>{html.escape(title)}</b> (Serial) ({year})\n"
            f"🎭 <b>Janr:</b> {html.escape(s_cfg['genres'])}\n"
            f"⭐ <b>IMDb:</b> {s_cfg['imdb_rating']}/10\n"
            f"🎬 <b>Rejissyor:</b> {html.escape(s_cfg['director'])}\n"
            f"👥 <b>Aktyorlar:</b> {html.escape(s_cfg['cast'])}\n\n"
            f"📝 <b>Tavsif:</b>\n<i>{html.escape(s_cfg['description'])}</i>\n\n"
            f"⬇️ <i>Serial qismlari shu yerga yuklanmoqda...</i>"
        )

        if card_media:
            banner_msg = await client.send_file(
                TARGET_SUPERGROUP,
                file=card_media,
                caption=banner_caption,
                reply_to=topic_id,
                parse_mode="html"
            )
        else:
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

        # DB ga SeriesModel va SourceModel yozish
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
                description=s_cfg["description"],
                imdb_rating=s_cfg["imdb_rating"],
                tmdb_id=s_cfg["tmdb_id"],
                release_year=year,
                director=s_cfg["director"],
                cast=s_cfg["cast"],
                source_id=src.id,
                source_type="asilmedia",
                status="completed",
                publish_status="published",
                is_18_plus=False
            )
            session.add(series_obj)
            await session.flush()
            series_id = series_obj.id

            for cat_id in s_cfg["category_ids"]:
                await session.execute(
                    insert(series_category_table).values(series_id=series_id, category_id=cat_id)
                )

            await session.commit()
            logger.info(f"✅ SeriesModel DB da yaratildi (Series ID: {series_id})")

    # Mavsumlarni olish yoki yaratish
    async with async_session_factory() as session:
        for s_num in allowed_seasons.keys():
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
            current_season_ids[s_num] = sid

    # 3. Mavjud qismlarni aniqlash
    existing_eps_by_season = {}
    async with async_session_factory() as session:
        for s_num, sid in current_season_ids.items():
            res = await session.execute(select(EpisodeModel.episode_number).where(EpisodeModel.season_id == sid))
            existing_eps_by_season[s_num] = set(res.scalars().all())

    # 4. Qismlarni ketma-ket yuklash (1 dan 55 gacha)
    total_target_episodes = sum(end - start + 1 for start, end in allowed_seasons.values())
    migrated_count = sum(len(eps) for eps in existing_eps_by_season.values())
    logger.info(f"Yuklanishi kerak bo'lgan jami qismlar: {total_target_episodes}. Mavjud: {migrated_count}")

    # Asilmediabot bilan ulanish
    last_received_ep_msg = None

    for s_num, (start_ep, end_ep) in allowed_seasons.items():
        sid = current_season_ids[s_num]
        logger.info(f"\n--- {s_num}-Mavsum: {start_ep}-{end_ep}-qismlar ---")

        for ep_num in range(start_ep, end_ep + 1):
            if ep_num in existing_eps_by_season[s_num]:
                logger.info(f"[MAVJUD] S{s_num:02d}E{ep_num:02d} allaqachon yuklangan, o'tkazib yuborildi.")
                continue

            # Botdan ep_num ni olish
            video_msg = None

            # 1. Tezkor usul: agar avvalgi qism xabarida '⏭ Keyingi qism' tugmasi bo'lsa
            if last_received_ep_msg and last_received_ep_msg.buttons:
                next_btn = None
                for r_idx, row in enumerate(last_received_ep_msg.buttons):
                    for c_idx, b in enumerate(row):
                        if "keyingi" in b.text.lower():
                            next_btn = (r_idx, c_idx)
                            break
                    if next_btn:
                        break

                if next_btn:
                    click_id = last_received_ep_msg.id
                    try:
                        await last_received_ep_msg.click(next_btn[0], next_btn[1])
                        replies = await poll_bot_response(client, ASIL_BOT, click_id, timeout=10.0, condition=lambda ms: any(m.file for m in ms))
                        for r in replies:
                            if r.file and (f"{ep_num}_qism" in (r.file.name or "").lower() or f"{ep_num}-qism" in (r.text or "").lower() or f"{ep_num} qism" in (r.text or "").lower()):
                                video_msg = r
                                break
                    except Exception as ce:
                        logger.warning(f"Keyingi qism tugmasini bosishda xatolik: {ce}")

            # 2. Zaxira usul: /start 11153 orqali qism raqamini sahifadan bosish
            if not video_msg:
                logger.info(f"Zaxira usul: /start {asil_id} orqali {ep_num}-qism tugmasini qidirish...")
                sent_init = await client.send_message(ASIL_BOT, f"/start {asil_id}")
                card_replies = await poll_bot_response(client, ASIL_BOT, sent_init.id, timeout=8.0, condition=lambda ms: any(m.buttons for m in ms))
                active_card = next((m for m in card_replies if m.buttons and any(b.text.strip().isdigit() for row in m.buttons for b in row)), None)

                if active_card:
                    # Qaysi sahifada ekanligini hisoblaymiz: 1-20 (p1), 21-40 (p2), 41-60 (p3)
                    target_page = ((ep_num - 1) // 20) + 1
                    current_page = 1

                    # Agar sahifaga o'tish kerak bo'lsa
                    for p in range(1, target_page):
                        # Keyingi sahifa tugmasini bosish
                        next_p_btn = None
                        for r_idx, row in enumerate(active_card.buttons):
                            for c_idx, b in enumerate(row):
                                if "▶️" in b.text or "➡️" in b.text:
                                    next_p_btn = (r_idx, c_idx)
                                    break
                            if next_p_btn:
                                break
                        if next_p_btn:
                            await active_card.click(next_p_btn[0], next_p_btn[1])
                            await asyncio.sleep(1.8)
                            active_card = await client.get_messages(ASIL_BOT, ids=active_card.id)

                    # Joriy sahifadan qism tugmasini topish
                    ep_btn = None
                    for r_idx, row in enumerate(active_card.buttons):
                        for c_idx, b in enumerate(row):
                            if b.text.strip() == str(ep_num):
                                ep_btn = (r_idx, c_idx)
                                break
                        if ep_btn:
                            break

                    if ep_btn:
                        click_id = active_card.id
                        await active_card.click(ep_btn[0], ep_btn[1])
                        replies = await poll_bot_response(client, ASIL_BOT, click_id, timeout=12.0, condition=lambda ms: any(m.file for m in ms))
                        video_msg = next((m for m in replies if m.file), None)

            if not video_msg:
                logger.error(f"❌ {ep_num}-qism videosini botdan olib bo'lmadi! Keyingi qismga o'tilmoqda...")
                continue

            last_received_ep_msg = video_msg
            ep_file_size = round(video_msg.file.size / 1024 / 1024, 1)

            # STORAGE kanalga jo'natish
            new_st_msg = await client.send_file(
                TARGET_STORAGE,
                file=video_msg.media,
                caption=(
                    f"🎬 <b>{html.escape(title)}</b>\n"
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
                file=new_st_msg.media,
                caption=(
                    f"🍿 <b>{html.escape(title)}</b>\n"
                    f"📺 <b>{s_num}-Mavsum | {ep_num}-Qism</b>\n\n"
                    f"🔹 <b>Format:</b> 720p HD\n"
                    f"🗣 <b>Til:</b> O'zbek tilida (Asilmedia)\n"
                    f"💾 <b>Hajmi:</b> {ep_file_size} MB"
                ),
                reply_to=topic_id,
                parse_mode="html"
            )

            # DB ga yozish (EpisodeModel + EpisodeTranslationModel)
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
                        break
                except Exception as dbe:
                    logger.warning(f"DB saqlashda xatolik: {dbe}. Qayta urinish {db_attempt+1}/5...")
                    await asyncio.sleep(3)

            migrated_count += 1
            logger.info(f"[{migrated_count}/{total_target_episodes}] [OK] {display_code} muvaffaqiyatli saqlandi! (ST Msg: {new_st_msg.id})")
            await asyncio.sleep(1.0)

    logger.info(f"MUVAFFAQIYAT: '{title}' seriali barcha {migrated_count}/{total_target_episodes} qismlar yakunlandi!")

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    logger.info("==================================================")
    logger.info("QASHQIRLAR MAKONI TO'LIQ MIGRATSIYA BOSHLANDI")
    logger.info(f"Kinolar soni: {len(MOVIES_CONFIG)}")
    logger.info(f"Serial: {SERIES_CONFIG['title']} (1 va 2-mavsumlar: 55 qism)")
    logger.info("==================================================")

    # 1. Filmlarni ko'chirish
    for m_cfg in MOVIES_CONFIG:
        try:
            await migrate_single_movie(client, m_cfg)
        except Exception as e:
            logger.error(f"[XATO] '{m_cfg['title']}' ni ko'chirishda xatolik: {e}", exc_info=True)

    # 2. Serialni ko'chirish
    try:
        await migrate_qashqirlar_series(client, SERIES_CONFIG)
    except Exception as e:
        logger.error(f"[XATO] Serialni ko'chirishda xatolik: {e}", exc_info=True)

    # Keshni tozalash
    try:
        from app.core.cache import delete_cache_pattern
        await delete_cache_pattern("movie*")
        await delete_cache_pattern("series*")
        await delete_cache_pattern("search*")
        await delete_cache_pattern("catalog*")
    except Exception:
        pass

    logger.info("\n==================================================")
    logger.info("BARCHA QASHQIRLAR MAKONI FILMLARI VA SERIALLARI YAKUNLANDI!")
    logger.info("==================================================")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
