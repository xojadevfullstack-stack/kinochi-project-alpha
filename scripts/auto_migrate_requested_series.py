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
import io
import re
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
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel, series_category_table
from app.infrastructure.db.models.source import SourceModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel
from sqlalchemy import select, insert
from telethon.tl.functions.messages import CreateForumTopicRequest, UpdatePinnedMessageRequest

class FlushStreamHandler(logging.StreamHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()

logger = logging.getLogger("batch_migrator")
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

REQUESTED_SERIES = [
    {
        "key": "house_of_dragon",
        "title": "Ajdar xonadoni",
        "original_title": "House of the Dragon",
        "tmdb_id": 94997,
        "release_year": 2022,
        "imdb_rating": 8.4,
        "topic_id": 317,
        "allowed_seasons": [1, 2],  # User explicitly requested: only up to season 2, do not upload season 3!
        "genres": "Drama, Fantastika, Sarguzasht, Jangari",
        "category_ids": [1, 3, 6, 8],
        "poster_url": "https://image.tmdb.org/t/p/w500/7V0Ebks0GgpKvQ7QbLAIdX5dos4.jpg",
        "trailer_url": "https://www.youtube.com/watch?v=DotnJ7tTA34",
        "director": "Ryan J. Condal, George R. R. Martin",
        "cast": "Matt Smith, Emma D'Arcy, Olivia Cooke, Rhys Ifans, Steve Toussaint, Eve Best",
        "description": (
            "Targaryenlar sulolasining oltin davri va ularning qudrati cho'qqisida turgan payti. "
            "Biroq taxt uchun boshlangan ichki nizo — 'Ajdarlar raqsi' sulolani va butun Vesterosni halokat yoqasiga olib keladi."
        )
    },
    {
        "key": "the_boys",
        "title": "Yigitlar",
        "original_title": "The Boys",
        "tmdb_id": 76479,
        "release_year": 2019,
        "imdb_rating": 8.7,
        "topic_id": 3665,
        "allowed_seasons": [1, 2, 3, 4],  # All 31 episodes
        "genres": "Jangari, Fantastika, Ilmiy fantastika, Komediya, Drama",
        "category_ids": [1, 3, 5, 6, 7],
        "poster_url": "https://image.tmdb.org/t/p/w500/in1R2dDc421JxsoRWaIIAqVI2KE.jpg",
        "trailer_url": "https://www.youtube.com/watch?v=06rueu_fh30",
        "director": "Eric Kripke",
        "cast": "Karl Urban, Jack Quaid, Antony Starr, Erin Moriarty, Dominique McElligott, Jessie T. Usher",
        "description": (
            "O'zlarining mashhurligi va qudratidan suiiste'mol qilayotgan soxta superqahramonlar va ularni "
            "boshqarayotgan qudratli 'Vought' korporatsiyasiga qarshi kurashuvchi oddiy insonlar guruhi."
        )
    },
    {
        "key": "breaking_bad",
        "title": "Mashaqqatlar sari",
        "original_title": "Breaking Bad",
        "tmdb_id": 1396,
        "release_year": 2008,
        "imdb_rating": 9.5,
        "topic_id": 957,
        "allowed_seasons": [1, 2, 3, 4, 5],  # All 62 episodes
        "genres": "Drama, Kriminal, Triller",
        "category_ids": [3, 4, 9],
        "poster_url": "https://image.tmdb.org/t/p/w500/anFx9aTOOYqgS3v7x3R84Kz67ly.jpg",
        "trailer_url": "https://www.youtube.com/watch?v=HhesaQXLuRY",
        "director": "Vince Gilligan",
        "cast": "Bryan Cranston, Aaron Paul, Anna Gunn, Dean Norris, Betsy Brandt, RJ Mitte, Bob Odenkirk",
        "description": (
            "Oddiy maktab kimyo o'qituvchisi Uolter Uayt og'ir xastalikka chalinganini bilgach, oilasining "
            "kelajagini ta'minlash maqsadida sobiq o'quvchisi Jessi Pinkman bilan birga metamfetamin ishlab "
            "chiqarishni boshlaydi va afsonaviy 'Xeyzenberg'ga aylanadi."
        )
    },
    {
        "key": "the_originals",
        "title": "Haqiqiylar",
        "original_title": "The Originals",
        "tmdb_id": 46896,
        "release_year": 2013,
        "imdb_rating": 8.3,
        "topic_id": 5392,
        "allowed_seasons": [1, 2],
        "genres": "Fantastika, Drama, Sirli",
        "category_ids": [3, 6, 10, 14],
        "poster_url": "https://image.tmdb.org/t/p/w500/keJOhJXGiLL54EW6QocbyvQGquA.jpg",
        "trailer_url": "https://www.youtube.com/watch?v=1b-3uV2Z2zE",
        "director": "Julie Plec",
        "cast": "Joseph Morgan, Daniel Gillies, Claire Holt, Phoebe Tonkin, Charles Michael Davis",
        "description": (
            "Dunyoning birinchi qadimiy vampirlar oilasi — Mayklsonlar o'zlari barpo etgan Yangi Orleanga qaytib, "
            "shahar ustidan nazoratni va oilaviy shon-sharafni tiklash uchun kurashadilar."
        )
    },
    {
        "key": "teen_wolf",
        "title": "Yosh bo'ri",
        "original_title": "Teen Wolf",
        "tmdb_id": 34524,
        "release_year": 2011,
        "imdb_rating": 7.7,
        "topic_id": 2876,
        "allowed_seasons": [1, 2, 3, 4, 5, 6],
        "genres": "Drama, Fantastika, Jangari",
        "category_ids": [1, 3, 6, 14],
        "poster_url": "https://image.tmdb.org/t/p/w500/wjKBTcNy1xihmExqJI8kM2qvavP.jpg",
        "trailer_url": "https://www.youtube.com/watch?v=1rCYDbefnmA",
        "director": "Jeff Davis",
        "cast": "Tyler Posey, Dylan O'Brien, Holland Roden, Shelley Hennig, Arden Cho, Linden Ashby",
        "description": (
            "Oddiy maktab o'quvchisi Skott Makkoll o'rmonda sirli bo'ri tomonidan tishlangach, o'zida "
            "g'ayritabiiy kuch va bo'riga aylanish qobiliyatini kashf etadi. U do'stlari bilan birga shaharni "
            "yovuz kuchlardan himoya qiladi."
        )
    },
    {
        "key": "vampire_diaries",
        "title": "Vampir kundaligi",
        "original_title": "The Vampire Diaries",
        "tmdb_id": 18165,
        "release_year": 2009,
        "imdb_rating": 7.7,
        "topic_id": 1195,
        "allowed_seasons": [1, 2, 3, 4, 5, 6, 7, 8],
        "genres": "Drama, Fantastika, Romantika",
        "category_ids": [3, 6, 13, 14],
        "poster_url": "https://image.tmdb.org/t/p/w500/gbp4zM0FE0n23X4UFY5EBlacrog.jpg",
        "trailer_url": "https://www.youtube.com/watch?v=BmVmhjjkN4E",
        "director": "Julie Plec, Kevin Williamson",
        "cast": "Paul Wesley, Ian Somerhalder, Nina Dobrev, Kat Graham, Candice King, Zach Roerig",
        "description": (
            "Misik-Folls shaharchasida yashovchi Elena Gilbert va asrlarga teng sirga ega bo'lgan aka-uka "
            "vampirlar — Stefan va Deymon Salvatore o'rtasidagi murakkab sevgi, sirlar va xavfli kurashlar girdobi."
        )
    }
]

async def fetch_poster_bytes(url: str) -> bytes | None:
    targets = [url]
    if "/original/" in url:
        targets.append(url.replace("/original/", "/w500/"))
    elif "/w500/" in url:
        targets.append(url.replace("/w500/", "/original/"))
        
    for u in targets:
        try:
            async with httpx.AsyncClient(timeout=12, follow_redirects=True) as hclient:
                res = await hclient.get(u)
                if res.status_code == 200 and len(res.content) > 1000:
                    return res.content
        except Exception:
            pass
    return None

async def create_or_find_topic(client: TelegramClient, title: str) -> int:
    clean_target = title.replace("🎬", "").split("(")[0].strip().lower()
    async for m in client.iter_messages(TARGET_SUPERGROUP, limit=300):
        if getattr(m, 'action', None) and type(m.action).__name__ == 'MessageActionTopicCreate':
            act_title = getattr(m.action, 'title', '').strip()
            clean_act = act_title.replace("🎬", "").split("(")[0].strip().lower()
            if clean_act == clean_target or clean_target in clean_act:
                logger.info(f"Mavjud topic topildi: '{act_title}' (ID: {m.id})")
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

async def extract_seasons_data(client: TelegramClient, topic_id: int) -> dict:
    all_msgs = []
    async for m in client.iter_messages(OLD_CHAT, reply_to=topic_id, reverse=True):
        all_msgs.append(m)

    video_msgs = [m for m in all_msgs if m.video or (m.document and m.file and m.file.mime_type and m.file.mime_type.startswith('video/'))]
    
    code_msgs = []
    for m in all_msgs:
        if m.text:
            match = re.search(r"S(\d+)[\-_]CH(\d+)", m.text, re.IGNORECASE)
            if match:
                s_num = int(match.group(1))
                ep_num = int(match.group(2))
                code_msgs.append((m.id, s_num, ep_num))

    mapping = {}
    if len(video_msgs) == len(code_msgs):
        for v, (_, s_num, ep_num) in zip(video_msgs, code_msgs):
            mapping.setdefault(s_num, []).append((ep_num, v.id))
    else:
        logger.warning(f"Topic {topic_id}: video soni ({len(video_msgs)}) va kod soni ({len(code_msgs)}) mos kelmadi!")
        # Fallback to pairing minimum count
        limit = min(len(video_msgs), len(code_msgs))
        for idx in range(limit):
            v = video_msgs[idx]
            _, s_num, ep_num = code_msgs[idx]
            mapping.setdefault(s_num, []).append((ep_num, v.id))

    return mapping

async def migrate_single_series(client: TelegramClient, cfg: dict):
    title = cfg["title"]
    original_title = cfg["original_title"]
    release_year = cfg["release_year"]
    imdb_rating = cfg["imdb_rating"]
    tmdb_id = cfg["tmdb_id"]
    genres = cfg["genres"]
    poster_url = cfg["poster_url"]
    description = cfg["description"]
    director = cfg["director"]
    cast = cfg["cast"]
    trailer_url = cfg.get("trailer_url")
    allowed_seasons = cfg.get("allowed_seasons")
    old_topic_id = cfg["topic_id"]

    logger.info(f"\n=======================================================")
    logger.info(f"BOSHLANMOQDA: {title} ({original_title}, {release_year})")
    logger.info(f"Eski Topic: {old_topic_id}")
    logger.info(f"=======================================================")

    # 1. Extract seasons data from old topic
    raw_seasons = await extract_seasons_data(client, old_topic_id)
    seasons_to_process = {}
    for s_num in sorted(raw_seasons.keys()):
        if allowed_seasons is not None and s_num not in allowed_seasons:
            logger.info(f"Mavsum {s_num} qoidalarga ko'ra o'tkazib yuboriladi (ruxsat etilgan: {allowed_seasons})")
            continue
        seasons_to_process[s_num] = raw_seasons[s_num]

    total_episodes_series = sum(len(eps) for eps in seasons_to_process.values())
    logger.info(f"Ko'chirilishi kerak bo'lgan jami qismlar: {total_episodes_series}")

    # 2. Topic ochish yoki DB dan olish
    topic_title = f"🎬 {title} ({release_year})"
    topic_id = None
    async with async_session_factory() as session:
        series_res = await session.execute(
            select(SeriesModel).where(SeriesModel.tmdb_id == tmdb_id)
        )
        existing_series = series_res.scalars().first()
        if existing_series and existing_series.source_id:
            src_chk = await session.get(SourceModel, existing_series.source_id)
            if src_chk and src_chk.topic_id:
                topic_id = src_chk.topic_id
                logger.info(f"Mavjud topic DB dan olindi: '{title}' (ID: {topic_id})")

    if not topic_id:
        topic_id = await create_or_find_topic(client, topic_title)
        logger.info(f"Topic tayyor! ID: {topic_id}")
    await asyncio.sleep(1.0)

    # 3. Database Series va Source tekshirish/yaratish
    current_series_id = None
    async with async_session_factory() as session:
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

        series_res = await session.execute(
            select(SeriesModel).where(SeriesModel.tmdb_id == tmdb_id)
        )
        series_obj = series_res.scalars().first()
        if not series_obj:
            series_obj = SeriesModel(
                title=title,
                description=description,
                status="completed",
                publish_status="published",
                is_18_plus=False,
                imdb_rating=imdb_rating,
                release_year=release_year,
                tmdb_id=tmdb_id,
                poster_url=poster_url,
                trailer_url=trailer_url,
                director=director,
                cast=cast,
                source_id=src.id,
                source_type="superguruh",
                custom_source_name="Kinochi @kinochi_mvp_bot"
            )
            session.add(series_obj)
            await session.flush()

            for cat_id in cfg.get("category_ids", []):
                try:
                    await session.execute(
                        insert(series_category_table).values(series_id=series_obj.id, category_id=cat_id)
                    )
                except Exception:
                    pass
            await session.commit()
            logger.info(f"'{title}' DB ga kiritildi (ID: {series_obj.id})")
        else:
            logger.info(f"'{title}' DB da mavjud (ID: {series_obj.id})")

        current_series_id = series_obj.id

    # 4. Banner jo'natish (agar hali bo'lmasa)
    has_banner = False
    async for m in client.iter_messages(TARGET_SUPERGROUP, reply_to=topic_id, limit=5):
        if m.photo or (m.text and title in m.text):
            has_banner = True
            break

    if not has_banner:
        logger.info(f"'{title}' uchun poster banner jo'natilmoqda...")
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

    # 5. Qismlarni birma-bir ko'chirish
    cur_ep_counter = 0
    migrated_series_count = 0

    for s_num in sorted(seasons_to_process.keys()):
        eps_list = seasons_to_process[s_num]
        logger.info(f"\n>>> {title} -> {s_num}-MAVSUM: {len(eps_list)} ta qism")

        current_season_id = None
        existing_ep_nums = set()
        async with async_session_factory() as session:
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
                    poster_url=poster_url,
                    episode_count=len(eps_list)
                )
                session.add(season_obj)
                await session.flush()
                await session.commit()
                logger.info(f"{s_num}-Mavsum DB da yaratildi (ID: {season_obj.id})")
            else:
                logger.info(f"{s_num}-Mavsum DB da mavjud (ID: {season_obj.id})")

            current_season_id = season_obj.id

            ep_res = await session.execute(
                select(EpisodeModel.episode_number).where(EpisodeModel.season_id == current_season_id)
            )
            existing_ep_nums = set(ep_res.scalars().all())

        for ep_num, old_ep_msg_id in eps_list:
            cur_ep_counter += 1
            display_code = f"S{s_num}-CH{ep_num}"

            # Check if episode already exists in DB
            if ep_num in existing_ep_nums:
                logger.info(f"[{cur_ep_counter}/{total_episodes_series}] [SKIP] {display_code} allaqachon ko'chirilgan.")
                migrated_series_count += 1
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
                f"📺 <b>{s_num}-Mavsum, {ep_num}-Qism</b>\n"
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
                        message=f"✅ **{ep_num}-qism** saqlandi va indekslandi. Kod: `{display_code}`",
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

            migrated_series_count += 1
            logger.info(f"[{cur_ep_counter}/{total_episodes_series}] [OK] {display_code} muvaffaqiyatli ko'chirildi (ST Msg ID: {new_st_msg.id})")

    # Invalidate cache for series
    try:
        from app.core.cache import delete_cache_pattern
        await delete_cache_pattern("series*")
        await delete_cache_pattern("search*")
        await delete_cache_pattern("catalog*")
    except Exception:
        pass

    logger.info(f"MUVAFFAQIYAT: '{title}' bo'yicha barcha {migrated_series_count}/{total_episodes_series} qismlar yakunlandi!")

async def main():
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")
    session_str = os.getenv("TELEGRAM_STRING_SESSION")

    client = TelegramClient(StringSession(session_str), api_id, api_hash)
    await client.connect()

    logger.info("==================================================")
    logger.info("AVTOMATIK SERIAL KO'CHIRISH SKRIPTI ISHGA TUSHDI")
    logger.info(f"Jami navbatdagi seriallar soni: {len(REQUESTED_SERIES)}")
    logger.info("==================================================")

    for idx, s_cfg in enumerate(REQUESTED_SERIES, start=1):
        logger.info(f"\n[SERIAL {idx}/{len(REQUESTED_SERIES)}]: {s_cfg['title']}")
        try:
            await migrate_single_series(client, s_cfg)
        except Exception as e:
            logger.error(f"[XATO] '{s_cfg['title']}' ni ko'chirishda xatolik yuz berdi: {e}", exc_info=True)
            logger.info("Keyingi serialga o'tilmoqda...")

    logger.info("\n==================================================")
    logger.info("BARCHA NAVBATDAGI SERIALLAR MUVAFFAQIYATLI KO'CHIRILDI!")
    logger.info("==================================================")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
