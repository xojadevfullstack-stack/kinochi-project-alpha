import logging
import re
import time
import uuid
import asyncio
from dataclasses import dataclass, field
import httpx
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from config import settings
from services.api_client import api_client

router = Router()
logger = logging.getLogger(__name__)

# Source-based locks to ensure strict sequential processing per channel/topic
source_locks: dict[str, asyncio.Lock] = {}

def get_source_lock(chat_id: int, topic_id: int | None) -> asyncio.Lock:
    key = f"{chat_id}:{topic_id or 0}"
    if key not in source_locks:
        source_locks[key] = asyncio.Lock()
    return source_locks[key]

# Regex patterns for episode number extraction
EPISODE_PATTERNS = [
    # 1. 'qism 8', 'qismi 8', 'seriya 8', 'qism: 8', 'chast 8'
    r'\b(?:qism|qismi|seriya|seriyasi|chast)[\s\-_:]*(\d{1,3})\b',
    # 2. '8-qism', '8 qism', '8_qism', '8-seriya'
    r'(?:^|[^a-zA-Z0-9])(\d{1,3})[\s\-_]*(?:qism|qismi|seriya|seriyasi|chast)\b',
    # 3. Xalqaro formatlar: S01E08, s1e1, E08, Ep 8, Episode 8
    r'(?:^|[^a-zA-Z0-9])S\d+[\s\-_]*E(\d{1,3})(?:[^a-zA-Z0-9]|$)',
    r'(?:^|[^a-zA-Z0-9])E(?:p(?:isode)?)?\.?\s*(\d{1,3})(?:[^a-zA-Z0-9]|$)',
    # 4. Faqat bitta sondan iborat matn: '8'
    r'^\s*(\d{1,3})\s*$',
    # 5. Fayl nomi formatlari: '08.mp4', '08_...mp4', 'Serial_08.mkv'
    r'(?:^|[^\d])0*(\d{1,3})\.(?:mp4|mkv|mov|avi|webm)$',
    r'^0*(\d{1,3})[\.\-_]',
    r'[\.\-_]0*(\d{1,3})\.(?:mp4|mkv|mov|avi|webm)$',
]

SEASON_PATTERNS = [
    r'(?:^|[^a-zA-Z0-9])(\d{1,3})[\s\-_]*(?:mavsum|fasl|sezon|season)\b',
    r'\b(?:mavsum|fasl|sezon|season)[\s\-_:]*(\d{1,3})\b',
    r'(?:^|[^a-zA-Z0-9])S(\d{1,3})[\s\-_]*E\d+(?:[^a-zA-Z0-9]|$)',
]

def extract_episode_num(caption: str | None, file_name: str | None) -> int | None:
    # 1. Check caption first (deliberate user label)
    if caption:
        for pat in EPISODE_PATTERNS[:5]:
            m = re.search(pat, caption, re.IGNORECASE)
            if m:
                return int(m.group(1))
    # 2. Check file_name
    if file_name:
        for pat in EPISODE_PATTERNS:
            m = re.search(pat, file_name, re.IGNORECASE)
            if m:
                return int(m.group(1))
    return None

def extract_season_num(caption: str | None, file_name: str | None) -> int | None:
    if caption:
        for pat in SEASON_PATTERNS:
            m = re.search(pat, caption, re.IGNORECASE)
            if m:
                return int(m.group(1))
    if file_name:
        for pat in SEASON_PATTERNS:
            m = re.search(pat, file_name, re.IGNORECASE)
            if m:
                return int(m.group(1))
    return None

async def process_single_video(message: Message, bot: Bot, pre_extracted_ep: int | None = None):
    chat_id = message.chat.id
    topic_id = message.message_thread_id

    # Extract file_id and file_name from video or document
    file_name = None
    if message.video:
        telegram_file_id = message.video.file_id
        file_name = message.video.file_name
    elif message.document:
        mime_type = message.document.mime_type or ""
        if not mime_type.startswith("video/"):
            await message.reply(f"❌ Yuborilgan fayl video emas (mime: {mime_type}).")
            return
        telegram_file_id = message.document.file_id
        file_name = message.document.file_name
    else:
        await message.reply("❌ Yuborilgan xabar video yoki document emas.")
        return

    caption = message.caption or ""

    # 1. Fresh lookup: Series by source
    url = f"/series/by-source?chat_id={chat_id}"
    if topic_id:
        url += f"&topic_id={topic_id}"
    resp = await api_client.client.get(url)
    if resp.status_code == 404:
        # 1.b Look up Movie by source
        movie_url = f"/movies/by-source?chat_id={chat_id}"
        if topic_id:
            movie_url += f"&topic_id={topic_id}"
        resp_movie = await api_client.client.get(movie_url)
        if resp_movie.status_code == 404:
            return
        try:
            resp_movie.raise_for_status()
        except httpx.HTTPStatusError as e:
            logger.error(f"Error fetching movie by source: {e}")
            await message.reply(f"❌ Kino backenddan qidirilayotganda tizimli xato (Status: {e.response.status_code})")
            return
        movie = resp_movie.json()

        # Copy video to storage channel
        try:
            storage_msg = await bot.copy_message(
                chat_id=settings.STORAGE_CHANNEL_ID,
                from_chat_id=chat_id,
                message_id=message.message_id
            )
            storage_msg_id = storage_msg.message_id
        except Exception as e:
            logger.error(f"Cannot copy message to storage: {e}")
            await message.reply("❌ Videoni Storage kanalga ko'chirib bo'lmadi (Bot admin emas yoki ruxsat yo'q).")
            return

        # Link video to movie
        try:
            resp = await api_client.client.post(f"/movies/{movie['id']}/link-video", json={
                "message_id": storage_msg_id,
                "language": "Asosiy",
                "telegram_file_id": telegram_file_id
            })
            resp.raise_for_status()
            await message.reply(f"✅ Kino videosi saqlandi va indekslandi. Kod: `{movie['code']}`", parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error linking video for movie {movie['id']}: {e}")
            await message.reply(f"❌ Kino bazaga qo'shildi, lekin videoni ulashda xatolik yuz berdi: {e}")
        return

    try:
        resp.raise_for_status()
    except httpx.HTTPStatusError as e:
        logger.error(f"Error fetching series by source: {e}")
        await message.reply(f"❌ Serial backenddan qidirilayotganda tizimli xato (Status: {e.response.status_code})")
        return
    series = resp.json()

    # 2. Get or create Season (supports explicit season from caption if present)
    target_season_num = extract_season_num(caption, file_name)
    seasons = series.get("seasons", [])
    season = None

    if target_season_num is not None:
        season = next((s for s in seasons if s.get("season_number") == target_season_num), None)
        if not season:
            try:
                resp = await api_client.client.post(f"/series/{series['id']}/seasons", json={
                    "series_id": series['id'],
                    "season_number": target_season_num,
                    "title": f"Mavsum {target_season_num}",
                    "status": "ongoing"
                })
                resp.raise_for_status()
                season = resp.json()
                seasons.append(season)
            except Exception as e:
                logger.error(f"Error creating season {target_season_num}: {e}")
                await message.reply(f"❌ {target_season_num}-mavsumni yaratishda tizimli xato yuz berdi.")
                return
    else:
        ongoing_seasons = [s for s in seasons if s.get("status") == "ongoing"]
        if ongoing_seasons:
            season = ongoing_seasons[-1]
        else:
            next_season_num = max([s.get("season_number", 0) for s in seasons], default=0) + 1
            try:
                resp = await api_client.client.post(f"/series/{series['id']}/seasons", json={
                    "series_id": series['id'],
                    "season_number": next_season_num,
                    "title": f"Mavsum {next_season_num}",
                    "status": "ongoing"
                })
                resp.raise_for_status()
                season = resp.json()
                seasons.append(season)
            except Exception as e:
                logger.error(f"Error creating season: {e}")
                await message.reply("❌ Yangi mavsum (season) yaratishda tizimli xato yuz berdi.")
                return

    season_id = season['id']

    # 3. Fresh fetch of episodes for this season inside lock
    try:
        resp = await api_client.client.get(f"/series/seasons/{season_id}/episodes")
        resp.raise_for_status()
        episodes = resp.json()
    except Exception as e:
        logger.error(f"Error fetching episodes: {e}")
        await message.reply("❌ Qismlarni (episodes) yuklashda tizimli xato yuz berdi.")
        return

    # 4. Hybrid Episode Number Resolution:
    # First, try to extract episode number from caption or filename
    ep_num = pre_extracted_ep if pre_extracted_ep is not None else extract_episode_num(caption, file_name)
    # Second, if neither caption nor filename has a number (clean video forward), use sequential forward order
    if ep_num is None:
        existing_nums = [e.get("episode_number", 0) for e in episodes]
        ep_num = max(existing_nums, default=0) + 1
        logger.info(f"Hybrid Mode: auto-assigned sequential episode number {ep_num} for msg {message.message_id}")

    storage_channel_id = settings.STORAGE_CHANNEL_ID
    if not storage_channel_id:
        logger.warning("STORAGE_CHANNEL_ID is not set. Cannot index.")
        await message.reply("❌ STORAGE_CHANNEL_ID sozlanmagan! Videoni saqlab bo'lmaydi.")
        return

    # Check if this episode already exists in the season (Upsert logic)
    existing_ep = next((e for e in episodes if e.get("episode_number") == ep_num), None)

    # If first episode ever of series or season, send poster/title
    is_first_series_ep = (len(seasons) == 1 and len(episodes) == 0 and not existing_ep)
    is_first_season_ep = (len(episodes) == 0 and not existing_ep)

    if is_first_series_ep:
        title_str = series.get('title') or "Noma'lum"
        post_caption = f"🎬 *{title_str}*\n\n"
        if series.get('description'):
            post_caption += f"{series.get('description')}\n"
        poster_url = series.get('poster_url')
        if poster_url:
            await bot.send_photo(storage_channel_id, photo=poster_url, caption=post_caption, parse_mode="Markdown")
        else:
            await bot.send_message(storage_channel_id, text=post_caption, parse_mode="Markdown")
    elif is_first_season_ep:
        season_title = season.get('title') or f"{season.get('season_number', 1)}-mavsum"
        await bot.send_message(storage_channel_id, text=f"📺 *{season_title}*", parse_mode="Markdown")

    # Copy video to storage channel with clean standardized caption (no random external channel ads)
    try:
        s_num = season.get('season_number', 1)
        storage_caption = f"🍿 <b>{series.get('title', '')}</b>\n📌 <b>{s_num}-mavsum, {ep_num}-qism</b>"
        msg = await bot.copy_message(
            storage_channel_id,
            from_chat_id=chat_id,
            message_id=message.message_id,
            caption=storage_caption,
            parse_mode="HTML"
        )
        storage_msg_id = msg.message_id
    except TelegramBadRequest as e:
        logger.error(f"Cannot copy message to storage: {e}")
        await message.reply("❌ Videoni Storage kanalga ko'chirib bo'lmadi (Bot admin emas yoki noto'g'ri).")
        return

    # Episode Creation or Retrieval with dual-layer conflict defense
    is_update = False
    if existing_ep:
        episode = existing_ep
        is_update = True
    else:
        code = str(uuid.uuid4())[:8]
        try:
            resp = await api_client.client.post(f"/series/seasons/{season_id}/episodes", json={
                "season_id": season_id,
                "episode_number": ep_num,
                "title": f"{ep_num}-qism",
                "code": code
            })
            resp.raise_for_status()
            episode = resp.json()
        except httpx.HTTPStatusError as e:
            # Layer 2 defense: in case of 400/409 duplicate conflict, re-fetch and upsert
            if e.response.status_code in (400, 409):
                logger.warning(f"Episode {ep_num} creation conflicted ({e.response.status_code}), re-fetching: {e}")
                refetch = await api_client.client.get(f"/series/seasons/{season_id}/episodes")
                refetch.raise_for_status()
                episodes = refetch.json()
                episode = next((e for e in episodes if e.get("episode_number") == ep_num), None)
                if not episode:
                    raise
                is_update = True
            else:
                raise

    # Link video to episode
    try:
        resp = await api_client.client.post(f"/series/episodes/{episode['id']}/link-video", json={
            "message_id": storage_msg_id,
            "language": "Asosiy",
            "telegram_file_id": telegram_file_id
        })
        resp.raise_for_status()
    except Exception as e:
        logger.error(f"Error linking video for episode {episode['id']}: {e}")
        await message.reply(f"❌ Qism bazada mavjud, lekin videoni ulashda xatolik yuz berdi: {e}")
        return

    # Check if season is complete
    expected_count = season.get("episode_count")
    if expected_count and ep_num >= expected_count:
        try:
            resp = await api_client.client.put(f"/series/seasons/{season_id}", json={
                "season_number": season.get("season_number"),
                "title": season.get("title"),
                "description": season.get("description"),
                "poster_url": season.get("poster_url"),
                "episode_count": expected_count,
                "status": "completed"
            })
            resp.raise_for_status()
        except Exception as e:
            logger.error(f"Error completing season: {e}")
            await message.reply(f"⚠️ Mavsum yakunlandi deb belgilashda xato: {e}")

    # Notify in source chat
    ep_code = episode.get("display_code") or episode.get("code") or code
    if is_update:
        await message.reply(f"🔄 <b>{ep_num}-qism</b> videosi yangilandi. Kod: <code>{ep_code}</code>", parse_mode="HTML")
    else:
        await message.reply(f"✅ <b>{ep_num}-qism</b> saqlandi va indekslandi. Kod: <code>{ep_code}</code>", parse_mode="HTML")


# ── BATCH BUFFER AGGREGATOR & DEBOUNCE ───────────────────────────────────────
DEBOUNCE_IDLE_SECONDS = 4.0   # Wait 4 seconds of idle time after the last video
MAX_BATCH_WAIT_SECONDS = 25.0 # Max batch collection window before forced processing

@dataclass
class SourceBatch:
    messages: list[Message] = field(default_factory=list)
    first_arrival: float = 0.0
    timer_task: asyncio.Task | None = None

source_batches: dict[str, SourceBatch] = {}

async def flush_source_batch(source_key: str, bot: Bot, delay: float):
    try:
        if delay > 0:
            await asyncio.sleep(delay)
    except asyncio.CancelledError:
        return

    # Extract chat_id and topic_id
    parts = source_key.split(":")
    chat_id = int(parts[0])
    topic_id = int(parts[1]) if len(parts) > 1 and parts[1] != "0" else None

    # Protect batch saving with source-level lock
    lock = get_source_lock(chat_id, topic_id)
    async with lock:
        batch = source_batches.pop(source_key, None)
        if not batch or not batch.messages:
            return

        messages = batch.messages

        # Extract episode number for each video and sort ascending (1, 2, 3... 10)
        items = []
        for msg in messages:
            fn = msg.video.file_name if msg.video else (msg.document.file_name if msg.document else "")
            ep_num = extract_episode_num(msg.caption, fn)
            # Tuple: (sort_key, message_id, ep_num, msg)
            items.append((ep_num if ep_num is not None else 999999, msg.message_id, ep_num, msg))

        # Strictly sort ascending by episode number, preserving message order for ties
        items.sort(key=lambda x: (x[0], x[1]))

        # Process each item sequentially with failure isolation
        for _, _, ep_num, msg in items:
            try:
                await process_single_video(msg, bot, pre_extracted_ep=ep_num)
            except Exception as e:
                logger.error(f"Error processing video msg {msg.message_id} in batch: {e}", exc_info=True)
                ep_label = f"{ep_num}-qism" if ep_num is not None else f"Xabar #{msg.message_id}"
                try:
                    await msg.reply(
                        f"❌ <b>{ep_label}</b>ni saqlashda xatolik yuz berdi: {e}\n<i>Qolgan qismlar davom ettirilmoqda...</i>",
                        parse_mode="HTML"
                    )
                except Exception:
                    pass

async def enqueue_video_message(message: Message, bot: Bot):
    chat_id = message.chat.id
    topic_id = message.message_thread_id or 0
    source_key = f"{chat_id}:{topic_id}"

    now = time.time()
    batch = source_batches.get(source_key)
    if not batch:
        batch = SourceBatch(first_arrival=now)
        source_batches[source_key] = batch

    batch.messages.append(message)

    elapsed = now - batch.first_arrival
    if elapsed >= MAX_BATCH_WAIT_SECONDS:
        # Max window reached: flush immediately
        if batch.timer_task and not batch.timer_task.done():
            batch.timer_task.cancel()
        batch.timer_task = asyncio.create_task(flush_source_batch(source_key, bot, delay=0.0))
    else:
        # Reset debounce timer
        if batch.timer_task and not batch.timer_task.done():
            batch.timer_task.cancel()
        remaining_max = MAX_BATCH_WAIT_SECONDS - elapsed
        delay = min(DEBOUNCE_IDLE_SECONDS, remaining_max)
        batch.timer_task = asyncio.create_task(flush_source_batch(source_key, bot, delay=delay))


@router.message(F.video | F.document)
async def auto_index_message(message: Message, bot: Bot):
    await enqueue_video_message(message, bot)

@router.channel_post(F.video | F.document)
async def auto_index_channel(message: Message, bot: Bot):
    await enqueue_video_message(message, bot)
