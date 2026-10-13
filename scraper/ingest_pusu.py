import sys, os
sys.path.insert(0, os.path.abspath('backend'))
sys.stdout.reconfigure(encoding='utf-8')
import asyncio
import logging
import html
import random
import re
from typing import Dict, Tuple, Optional
from telethon import TelegramClient, errors
from telethon.tl.functions.messages import CreateForumTopicRequest
from telethon.utils import pack_bot_file_id
from telethon.sessions import StringSession

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel
from app.infrastructure.db.models.source import SourceModel
from app.infrastructure.db.repositories.series_repository import SeriesRepository
from app.application.series.series_service import SeriesService
from app.domain.series.entities import EpisodeCreate, SeasonCreate
from scraper.config import TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_STRING_SESSION, AUTO_TOPIC_CHAT_ID, STORAGE_CHANNEL_ID

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_pusu")

SERIES_ID = 892

# TMDb Season ranges (10 seasons, 300 episodes):
SEASONS_MAP = {
    1: (1, 9),
    2: (10, 41),
    3: (42, 63),
    4: (64, 93),
    5: (94, 128),
    6: (129, 161),
    7: (162, 195),
    8: (196, 229),
    9: (230, 263),
    10: (264, 300),
}

async def build_episode_source_map(client: TelegramClient) -> Dict[int, Tuple[str, int]]:
    """
    Maps each episode number (1..300) to (channel_username, msg_id).
    """
    logger.info("Indexing episode source messages across Telegram channels...")
    source_map: Dict[int, Tuple[str, int]] = {}

    # 1. Main channel: @Qashqirlar_Makoni_Uzbekchada
    main_ch = "Qashqirlar_Makoni_Uzbekchada"
    entity = await client.get_entity(main_ch)
    async for m in client.iter_messages(entity, limit=2000):
        if not m.file:
            continue
        fname = m.file.name or ""
        txt = (m.text or "").replace('\n', ' ')
        mime = getattr(m.file, 'mime_type', '') or ''
        if not (mime.startswith('video') or fname.endswith(('.mp4', '.mkv', '.avi', '.mov'))):
            continue
        if "Kurtlar Vadisi" in fname and "Bölüm" in fname:
            continue

        m_ep = None
        m1 = re.search(r'(\d+)\s*[-_]?\s*qism\s*pistirma', txt, re.I)
        if m1:
            m_ep = int(m1.group(1))
        if not m_ep:
            m2 = re.search(r'pistirma[^\d]*(\d+)\s*[-_]?\s*qism', txt, re.I)
            if m2:
                m_ep = int(m2.group(1))
        if not m_ep:
            m3 = re.search(r'Pistirma[^\d]*(\d+)', fname, re.I)
            if m3:
                m_ep = int(m3.group(1))
        if not m_ep:
            m4 = re.search(r'(\d+)\s*[-_]?\s*qism', txt, re.I)
            if m4 and any(k in txt.lower() for k in ["pistirma", "pusu", "tuzoq"]):
                m_ep = int(m4.group(1))
        if not m_ep:
            m5 = re.match(r'^(\d+)\.mp4$', fname.strip(), re.I)
            if m5 and int(m5.group(1)) > 97:
                m_ep = int(m5.group(1))

        if m_ep and (m_ep not in source_map):
            source_map[m_ep] = (main_ch, m.id)

    # Combined episodes in main channel
    source_map[281] = (main_ch, 1188)
    source_map[282] = (main_ch, 1188)
    source_map[283] = (main_ch, 1189)
    source_map[284] = (main_ch, 1189)

    # 2. Episode 202 from @qashqirlar_makoni_films
    source_map[202] = ("qashqirlar_makoni_films", 15039)

    # 3. Final episodes 297..300 from @Qashqirlar_Makoni_Pusu_Film
    source_map[298] = ("Qashqirlar_Makoni_Pusu_Film", 433)
    source_map[299] = ("Qashqirlar_Makoni_Pusu_Film", 434)
    source_map[300] = ("Qashqirlar_Makoni_Pusu_Film", 435)

    logger.info(f"Source map built: {len(source_map)} / 300 episodes available.")
    return source_map

async def get_or_create_topic(client: TelegramClient) -> int:
    async with async_session_factory() as session:
        s_obj = await session.get(SeriesModel, SERIES_ID)
        if s_obj and s_obj.source_id:
            src = await session.get(SourceModel, s_obj.source_id)
            if src and src.topic_id and src.topic_id != 33073:
                return src.topic_id

    # Create new clean topic
    peer = await client.get_input_entity(AUTO_TOPIC_CHAT_ID)
    topic_name = "🎬 Kurtlar Vadisi: Pusu (Qashqirlar makoni: Pistirma)"
    res = await client(CreateForumTopicRequest(
        peer=peer,
        title=topic_name,
        random_id=random.randint(1, 2**31 - 1)
    ))
    topic_id = None
    for u in getattr(res, 'updates', []):
        if hasattr(u, 'message') and hasattr(u.message, 'id'):
            topic_id = u.message.id
            break
        elif hasattr(u, 'id'):
            topic_id = u.id

    if not topic_id:
        topic_id = 33073

    async with async_session_factory() as session:
        src = SourceModel(
            name="Qashqirlar makoni: Pistirma",
            type="superguruh",
            chat_id=int(AUTO_TOPIC_CHAT_ID),
            topic_id=int(topic_id)
        )
        session.add(src)
        await session.flush()
        s_obj = await session.get(SeriesModel, SERIES_ID)
        if s_obj:
            s_obj.source_id = src.id
            s_obj.title = "Qashqirlar makoni: Pistirma (Kurtlar Vadisi: Pusu)"
        await session.commit()

    logger.info(f"Forum topic ready: ID={topic_id}")
    return topic_id

async def get_or_create_season(season_num: int) -> int:
    async with async_session_factory() as session:
        series_repo = SeriesRepository(session)
        all_seasons = await series_repo.get_seasons_by_series(SERIES_ID)
        matched = next((s for s in all_seasons if s.season_number == season_num), None)
        if matched:
            return matched.id
        
        start_ep, end_ep = SEASONS_MAP.get(season_num, (1, 1))
        count = end_ep - start_ep + 1
        series_service = SeriesService(repository=series_repo, telegram_api=None)
        created = await series_service.create_season(SeasonCreate(
            series_id=SERIES_ID,
            season_number=season_num,
            title=f"{season_num}-Mavsum"
        ))
        await session.commit()
        logger.info(f"Created Season {season_num} in DB (ID: {created.id})")
        return created.id

async def ingest_single_episode(
    client: TelegramClient,
    season_id: int,
    season_num: int,
    ep_num: int,
    source_ch: str,
    source_msg_id: int,
    topic_id: int
) -> bool:
    # 1. Check if already exists in DB
    async with async_session_factory() as session:
        from sqlalchemy import text
        res = await session.execute(
            text("SELECT id FROM episodes WHERE season_id = :sid AND episode_number = :ep"),
            {"sid": season_id, "ep": ep_num}
        )
        if res.scalar():
            logger.info(f"  ⏭️ Season {season_num} Ep {ep_num} allaqachon bazada mavjud. O'tkazib yuborildi.")
            return True

    # 2. Fetch source message
    try:
        src_msg = await client.get_messages(source_ch, ids=source_msg_id)
    except Exception as e:
        logger.error(f"Error fetching source msg {source_msg_id} from @{source_ch}: {e}")
        return False

    if not src_msg or not src_msg.media:
        logger.error(f"Source msg {source_msg_id} in @{source_ch} has no media!")
        return False

    topic_cap = f"🍿 <b>Qashqirlar makoni: Pistirma</b>\n📺 <b>{season_num}-Mavsum | {ep_num}-Qism</b>"
    storage_cap = f"🍿 <b>Qashqirlar makoni: Pistirma</b>\n📺 {season_num}-Mavsum {ep_num}-Qism\n🆔 Series #{SERIES_ID}"

    # 3. Copy to Topic (with FloodWait handling)
    topic_msg = None
    for attempt in range(3):
        try:
            topic_msg = await client.send_file(
                AUTO_TOPIC_CHAT_ID,
                file=src_msg.media,
                caption=topic_cap,
                reply_to=topic_id,
                supports_streaming=True,
                parse_mode="html"
            )
            break
        except errors.FloodWaitError as fwe:
            logger.warning(f"⏳ FloodWait in topic copy: sleeping {fwe.seconds + 2}s...")
            await asyncio.sleep(fwe.seconds + 2)
        except Exception as e:
            logger.error(f"Error copying to topic: {e}")
            await asyncio.sleep(3)

    if not topic_msg:
        logger.error(f"Failed to copy Ep {ep_num} to topic!")
        return False

    # Short pause between channel calls
    await asyncio.sleep(1.5)

    # 4. Copy to Storage Channel (with FloodWait handling)
    storage_msg = None
    for attempt in range(3):
        try:
            storage_msg = await client.send_file(
                STORAGE_CHANNEL_ID,
                file=src_msg.media,
                caption=storage_cap,
                supports_streaming=True,
                parse_mode="html"
            )
            break
        except errors.FloodWaitError as fwe:
            logger.warning(f"⏳ FloodWait in storage copy: sleeping {fwe.seconds + 2}s...")
            await asyncio.sleep(fwe.seconds + 2)
        except Exception as e:
            logger.error(f"Error copying to storage: {e}")
            await asyncio.sleep(3)

    if not storage_msg:
        logger.error(f"Failed to copy Ep {ep_num} to storage!")
        return False

    # 5. Pack bot file ID and save to DB
    bot_file_id = None
    try:
        if storage_msg.media:
            bot_file_id = pack_bot_file_id(storage_msg.media)
    except Exception:
        pass

    async with async_session_factory() as session:
        series_repo = SeriesRepository(session)
        series_service = SeriesService(repository=series_repo, telegram_api=None)

        ep_entity = await series_service.create_episode(EpisodeCreate(
            season_id=season_id,
            episode_number=ep_num,
            title=f"{ep_num}-qism"
        ))
        await series_repo.add_episode_translation(
            episode_id=ep_entity.id,
            language="Asosiy",
            telegram_file_id=bot_file_id,
            storage_channel_message_id=storage_msg.id
        )
        await session.commit()

    logger.info(f"  ✅ Season {season_num} Ep {ep_num} muvaffaqiyatli saqlandi! (Topic #{topic_msg.id}, Storage #{storage_msg.id})")
    return True

async def run_ingest(season_target: Optional[int] = None, max_eps_per_run: Optional[int] = None):
    client = TelegramClient(StringSession(TELEGRAM_STRING_SESSION), TELEGRAM_API_ID, TELEGRAM_API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        print("Client not authorized!")
        return

    source_map = await build_episode_source_map(client)
    topic_id = await get_or_create_topic(client)

    seasons_to_process = [season_target] if season_target else list(SEASONS_MAP.keys())
    
    total_uploaded = 0
    for s_num in seasons_to_process:
        start_ep, end_ep = SEASONS_MAP[s_num]
        season_id = await get_or_create_season(s_num)
        logger.info(f"\n==========================================")
        logger.info(f"📺 MAVSUM {s_num}: Qismlar {start_ep}..{end_ep}")
        logger.info(f"==========================================")

        for ep in range(start_ep, end_ep + 1):
            if max_eps_per_run and total_uploaded >= max_eps_per_run:
                logger.info(f"Belgilangan maksimal limitga yetildi ({total_uploaded} qism). To'xtatildi.")
                await client.disconnect()
                return

            if ep not in source_map:
                logger.warning(f"⚠️ Ep {ep} source_map da topilmadi! O'tkazib yuborildi.")
                continue

            src_ch, src_mid = source_map[ep]
            success = await ingest_single_episode(
                client=client,
                season_id=season_id,
                season_num=s_num,
                ep_num=ep,
                source_ch=src_ch,
                source_msg_id=src_mid,
                topic_id=topic_id
            )
            if success:
                total_uploaded += 1
            # Adaptive delay to respect Telegram limits
            await asyncio.sleep(2.5)

    logger.info(f"\n🎉 Ingestion yakunlandi! Jami {total_uploaded} ta qism muvaffaqiyatli yuklandi.")
    await client.disconnect()

if __name__ == "__main__":
    target_s = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else None
    asyncio.run(run_ingest(season_target=target_s))
