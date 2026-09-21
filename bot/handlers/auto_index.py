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

# Regex patterns for explicit episode number in caption ONLY (no filename matching)
CAPTION_EPISODE_PATTERNS = [
    # 1. '8-qism', '8 qism', '8_qism', '8-seriya', '8 seriya'
    r'(?:^|[^a-zA-Z0-9])(\d{1,3})[\s\-_]*(?:qism|qismi|seriya|seriyasi|chast)\b',
    # 2. 'qism 8', 'qismi 8', 'seriya 8', 'qism: 8', 'chast 8'
    r'\b(?:qism|qismi|seriya|seriyasi|chast)[\s\-_:]*(\d{1,3})\b',
    # 3. S01E08, s1e1, E08, Ep 8, Episode 8
    r'(?:^|[^a-zA-Z0-9])S\d+[\s\-_]*E(\d{1,3})(?:[^a-zA-Z0-9]|$)',
    r'(?:^|[^a-zA-Z0-9])E(?:p(?:isode)?)?\.?\s*(\d{1,3})(?:[^a-zA-Z0-9]|$)',
    # 4. Faqat bitta sondan iborat qisqa xabar: '8'
    r'^\s*(\d{1,3})\s*$',
]

CAPTION_SEASON_PATTERNS = [
    r'(?:^|[^a-zA-Z0-9])(\d{1,3})[\s\-_]*(?:mavsum|fasl|sezon|season)\b',
    r'\b(?:mavsum|fasl|sezon|season)[\s\-_:]*(\d{1,3})\b',
    r'(?:^|[^a-zA-Z0-9])S(\d{1,3})[\s\-_]*E\d+(?:[^a-zA-Z0-9]|$)',
]

def extract_episode_num_from_caption(caption: str | None) -> int | None:
    """Faqatgina caption'dan aniq qism raqamini oladi (file_name tekshirilmaydi)."""
    if not caption:
        return None
    for pat in CAPTION_EPISODE_PATTERNS:
        m = re.search(pat, caption, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None

def extract_season_num_from_caption(caption: str | None) -> int | None:
    """Caption'dan mavsum raqamini aniqlash."""
    if not caption:
        return None
    for pat in CAPTION_SEASON_PATTERNS:
        m = re.search(pat, caption, re.IGNORECASE)
        if m:
            return int(m.group(1))
    return None

def extract_media_info(message: Message) -> tuple[str | None, str | None]:
    """Videodan telegram_file_id va file_name oladi."""
    if message.video:
        return message.video.file_id, message.video.file_name
    elif message.document:
        mime_type = message.document.mime_type or ""
        if mime_type.startswith("video/"):
            return message.document.file_id, message.document.file_name
    return None, None


async def process_movie_message(message: Message, bot: Bot, movie: dict):
    telegram_file_id, _ = extract_media_info(message)
    if not telegram_file_id:
        try:
            await message.reply("❌ Yuborilgan fayl video emas yoki video formati qo'llab-quvvatlanmaydi.")
        except Exception:
            pass
        return

    # Copy video to storage channel
    try:
        storage_msg = await bot.copy_message(
            chat_id=settings.STORAGE_CHANNEL_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id
        )
        storage_msg_id = storage_msg.message_id
    except Exception as e:
        logger.error(f"Cannot copy movie message to storage: {e}")
        try:
            await message.reply("❌ Videoni Storage kanalga ko'chirib bo'lmadi (Bot admin emas yoki ruxsat yo'q).")
        except Exception:
            pass
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
        try:
            await message.reply(f"❌ Kino bazaga qo'shildi, lekin videoni ulashda xatolik yuz berdi: {e}")
        except Exception:
            pass


async def process_series_batch(messages: list[Message], bot: Bot, series: dict):
    storage_channel_id = settings.STORAGE_CHANNEL_ID
    if not storage_channel_id:
        logger.warning("STORAGE_CHANNEL_ID is not set.")
        for msg in messages:
            try:
                await msg.reply("❌ STORAGE_CHANNEL_ID sozlanmagan! Videoni saqlab bo'lmaydi.")
            except Exception:
                pass
        return

    seasons = series.get("seasons", [])
    
    # Check if any message in batch specifies an explicit season in caption
    target_season_num = None
    for msg in messages:
        s_num = extract_season_num_from_caption(msg.caption)
        if s_num is not None:
            target_season_num = s_num
            break

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
                for msg in messages:
                    try:
                        await msg.reply(f"❌ {target_season_num}-mavsumni yaratishda xato: {e}")
                    except Exception:
                        pass
                return
    else:
        ongoing_seasons = [s for s in seasons if s.get("status") == "ongoing"]
        if ongoing_seasons:
            season = ongoing_seasons[-1]
        elif seasons:
            season = seasons[-1]
        else:
            # First season creation
            try:
                resp = await api_client.client.post(f"/series/{series['id']}/seasons", json={
                    "series_id": series['id'],
                    "season_number": 1,
                    "title": "Mavsum 1",
                    "status": "ongoing"
                })
                resp.raise_for_status()
                season = resp.json()
                seasons.append(season)
            except Exception as e:
                logger.error(f"Error creating Season 1: {e}")
                for msg in messages:
                    try:
                        await msg.reply(f"❌ 1-mavsumni yaratishda xato: {e}")
                    except Exception:
                        pass
                return

    season_id = season['id']

    # ── BOSQICH A — RESERVE (copy_message'dan OLDIN, hech qanday Telegram network chaqiruvisiz) ──
    reservation_items = []
    for msg in messages:
        explicit_ep = extract_episode_num_from_caption(msg.caption)
        reservation_items.append({
            "source_message_id": msg.message_id,
            "explicit_episode_number": explicit_ep,
            "title": f"{explicit_ep}-qism" if explicit_ep else None
        })

    recv_ts = time.time()
    reserved_episodes = await api_client.reserve_episodes(season_id, reservation_items)
    if not reserved_episodes:
        logger.error(f"Failed to reserve episodes for season {season_id}")
        for msg in messages:
            try:
                await msg.reply("❌ Qismlarni DB'da band qilishda tizimli xato yuz berdi.")
            except Exception:
                pass
        return

    # Map reserved episodes by source_message_id
    reserved_map = {item["source_message_id"]: item for item in reserved_episodes}

    # Logging: [ORDER_AUDIT] status=RESERVED
    for item in reserved_episodes:
        logger.info(
            f"[ORDER_AUDIT] msg_id={item['source_message_id']} | "
            f"recv_ts={recv_ts:.3f} | "
            f"reserved_ep={item['episode_number']} | "
            f"code={item['display_code']} | "
            f"status=RESERVED"
        )

    # First series/season banner in storage channel
    is_first_series_ep = (len(seasons) == 1 and reserved_episodes and reserved_episodes[0]["episode_number"] == 1 and not reserved_episodes[0].get("is_update"))
    is_first_season_ep = (reserved_episodes and reserved_episodes[0]["episode_number"] == 1 and not reserved_episodes[0].get("is_update"))

    if is_first_series_ep:
        title_str = series.get('title') or "Noma'lum"
        post_caption = f"🎬 *{title_str}*\n\n"
        if series.get('description'):
            post_caption += f"{series.get('description')}\n"
        poster_url = series.get('poster_url')
        try:
            if poster_url:
                await bot.send_photo(storage_channel_id, photo=poster_url, caption=post_caption, parse_mode="Markdown")
            else:
                await bot.send_message(storage_channel_id, text=post_caption, parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Could not send series banner to storage: {e}")
    elif is_first_season_ep:
        season_title = season.get('title') or f"{season.get('season_number', 1)}-mavsum"
        try:
            await bot.send_message(storage_channel_id, text=f"📺 *{season_title}*", parse_mode="Markdown")
        except Exception as e:
            logger.warning(f"Could not send season banner to storage: {e}")

    # ── BOSQICH B — UPLOAD (endi xavfsiz parallel yoki ketma-ket, order bazada band) ──
    s_num = season.get('season_number', 1)
    series_title = series.get('title', '')

    for msg in messages:
        reserved_info = reserved_map.get(msg.message_id)
        if not reserved_info:
            continue

        ep_num = reserved_info["episode_number"]
        ep_id = reserved_info["id"]
        ep_code = reserved_info["display_code"]
        is_update = reserved_info.get("is_update", False)

        telegram_file_id, _ = extract_media_info(msg)
        if not telegram_file_id:
            try:
                await msg.reply(f"❌ <b>{ep_num}-qism</b>: Yuborilgan fayl video emas.", parse_mode="HTML")
            except Exception:
                pass
            continue

        storage_caption = f"🍿 <b>{series_title}</b>\n📌 <b>{s_num}-mavsum, {ep_num}-qism</b>"

        # Copy to storage channel
        try:
            copied = await bot.copy_message(
                chat_id=storage_channel_id,
                from_chat_id=msg.chat.id,
                message_id=msg.message_id,
                caption=storage_caption,
                parse_mode="HTML"
            )
            storage_msg_id = copied.message_id
        except Exception as e:
            logger.error(f"[ORDER_AUDIT] msg_id={msg.message_id} | status=FAILED | error={e}")
            try:
                await msg.reply(
                    f"⚠️ <b>{ep_num}-qism</b> bazada band qilindi ({ep_code}), lekin videoni Storage kanalga ko'chirishda xatolik: {e}",
                    parse_mode="HTML"
                )
            except Exception:
                pass
            continue

        # Link video to reserved episode
        try:
            resp = await api_client.client.post(f"/series/episodes/{ep_id}/link-video", json={
                "message_id": storage_msg_id,
                "language": "Asosiy",
                "telegram_file_id": telegram_file_id
            })
            resp.raise_for_status()
            logger.info(
                f"[ORDER_AUDIT] msg_id={msg.message_id} | "
                f"db_write_ts={time.time():.3f} | "
                f"final_ep={ep_num} | "
                f"code={ep_code} | "
                f"status=DB_COMMITTED"
            )
            if is_update:
                await msg.reply(f"🔄 <b>{ep_num}-qism</b> videosi yangilandi. Kod: <code>{ep_code}</code>", parse_mode="HTML")
            else:
                await msg.reply(f"✅ <b>{ep_num}-qism</b> saqlandi va indekslandi. Kod: <code>{ep_code}</code>", parse_mode="HTML")
        except Exception as e:
            logger.error(f"Error linking video for episode {ep_id}: {e}")
            try:
                await msg.reply(f"❌ <b>{ep_num}-qism</b> videosini ulashda xatolik yuz berdi: {e}", parse_mode="HTML")
            except Exception:
                pass

    # Check if season is complete (only if all expected episodes are present)
    expected_count = season.get("episode_count")
    if expected_count and len(reserved_episodes) >= expected_count and season.get("status") != "completed":
        try:
            await api_client.client.put(f"/series/seasons/{season_id}", json={
                "season_number": season.get("season_number"),
                "title": season.get("title"),
                "description": season.get("description"),
                "poster_url": season.get("poster_url"),
                "episode_count": expected_count,
                "status": "completed"
            })
        except Exception as e:
            logger.warning(f"Error marking season {season_id} as completed: {e}")



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

    parts = source_key.split(":")
    chat_id = int(parts[0])
    topic_id = int(parts[1]) if len(parts) > 1 and parts[1] != "0" else None

    # Protect batch saving with source-level lock
    lock = get_source_lock(chat_id, topic_id)
    async with lock:
        batch = source_batches.pop(source_key, None)
        if not batch or not batch.messages:
            return

        # 1. Telegram xabarlarini message_id bo'yicha o'sish tartibida saralash (1-qismdan boshlab)
        messages = sorted(batch.messages, key=lambda m: m.message_id)

        # 2. Source orqali Series yoki Movie qidirish
        url = f"/series/by-source?chat_id={chat_id}"
        if topic_id:
            url += f"&topic_id={topic_id}"
        resp = await api_client.client.get(url)

        if resp.status_code == 404:
            # Movie tekshirish
            movie_url = f"/movies/by-source?chat_id={chat_id}"
            if topic_id:
                movie_url += f"&topic_id={topic_id}"
            resp_movie = await api_client.client.get(movie_url)
            if resp_movie.status_code == 404:
                return
            try:
                resp_movie.raise_for_status()
                movie = resp_movie.json()
            except Exception as e:
                logger.error(f"Error fetching movie by source: {e}")
                return

            for msg in messages:
                await process_movie_message(msg, bot, movie)
            return

        try:
            resp.raise_for_status()
            series = resp.json()
        except Exception as e:
            logger.error(f"Error fetching series by source: {e}")
            for msg in messages:
                try:
                    await msg.reply(f"❌ Serial backenddan qidirilayotganda tizimli xato: {e}")
                except Exception:
                    pass
            return

        # 3. Series uchun qismlarni ketma-ket indekslash
        await process_series_batch(messages, bot, series)


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
