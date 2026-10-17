import html
import logging
import re
import time
import uuid
import asyncio
from dataclasses import dataclass, field
import httpx
from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest, TelegramRetryAfter
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


async def safe_copy_message_with_retry(
    bot: Bot,
    chat_id: int | str,
    from_chat_id: int | str,
    message_id: int,
    caption: str | None = None,
    parse_mode: str | None = "HTML",
    notify_msg: Message | None = None,
    item_label: str = "video",
    max_retries: int = 5
) -> Message:
    """
    Kanalga xabarni nusxalash (copy_message). Telegram Flood control (429 Too Many Requests)
    cheklovi yuz berganda avtomatik kutiladi va qayta uriniladi.
    """
    for attempt in range(max_retries):
        try:
            return await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=from_chat_id,
                message_id=message_id,
                caption=caption,
                parse_mode=parse_mode
            )
        except TelegramRetryAfter as e:
            wait_seconds = int(e.retry_after) + 2
            logger.warning(
                f"[FLOOD_CONTROL] Telegram Flood control hit: retry after {wait_seconds}s "
                f"(attempt {attempt + 1}/{max_retries}) for msg_id={message_id}"
            )
            wait_msg = None
            if notify_msg:
                try:
                    wait_msg = await notify_msg.reply(
                        f"⏳ <b>Telegram cheklovi (Flood control):</b> {item_label} Storage kanalga ko'chirilishi uchun "
                        f"Telegram {wait_seconds} soniya tanaffus talab qildi.\n"
                        f"Kutilmoqda, vaqt tugagach yuklash avtomatik davom etadi...",
                        parse_mode="HTML"
                    )
                except Exception as reply_err:
                    logger.debug(f"Flood control xabarini yuborishda xatolik: {reply_err}")

            await asyncio.sleep(wait_seconds)

            if wait_msg:
                try:
                    await wait_msg.delete()
                except Exception as del_err:
                    logger.debug(f"Flood control xabarini o'chirishda xatolik: {del_err}")
        except Exception:
            raise

    raise Exception(f"Telegram flood control cheklovi sababli {max_retries} marta urinishdan so'ng ham yuklab bo'lmadi.")


async def safe_send_message_with_retry(
    bot: Bot,
    chat_id: int | str,
    text: str,
    parse_mode: str | None = "Markdown",
    max_retries: int = 3
):
    for attempt in range(max_retries):
        try:
            return await bot.send_message(chat_id=chat_id, text=text, parse_mode=parse_mode)
        except TelegramRetryAfter as e:
            wait_seconds = int(e.retry_after) + 2
            logger.warning(f"[FLOOD_CONTROL] send_message retry after {wait_seconds}s")
            await asyncio.sleep(wait_seconds)
        except Exception:
            raise


async def safe_send_photo_with_retry(
    bot: Bot,
    chat_id: int | str,
    photo: str,
    caption: str | None = None,
    parse_mode: str | None = "Markdown",
    max_retries: int = 3
):
    for attempt in range(max_retries):
        try:
            return await bot.send_photo(chat_id=chat_id, photo=photo, caption=caption, parse_mode=parse_mode)
        except TelegramRetryAfter as e:
            wait_seconds = int(e.retry_after) + 2
            logger.warning(f"[FLOOD_CONTROL] send_photo retry after {wait_seconds}s")
            await asyncio.sleep(wait_seconds)
        except Exception:
            raise


async def process_movie_message(message: Message, bot: Bot, movie: dict):
    telegram_file_id, _ = extract_media_info(message)
    if not telegram_file_id:
        try:
            await message.reply("❌ Yuborilgan fayl video emas yoki video formati qo'llab-quvvatlanmaydi.")
        except Exception as reply_err:
            logger.debug(f"Foydalanuvchiga xato xabarini yuborishda muammo: {reply_err}")
        return

    movie_title = html.escape(movie.get("title") or "Noma'lum kino")
    movie_code = movie.get("code")
    release_year = movie.get("release_year")

    caption_lines = [f"🍿 <b>{movie_title}</b>"]
    if movie_code:
        caption_lines.append(f"🔑 <b>Kodi:</b> <code>{movie_code}</code>")
    if release_year:
        caption_lines.append(f"📅 <b>Yili:</b> {release_year}")
    storage_caption = "\n".join(caption_lines)

    # NO OVERWRITES: Agar filmda O'zbekcha video tarjimasi allaqachon mavjud bo'lsa, tashlab yuboramiz
    existing_translations = movie.get("translations", []) or []
    has_video = any(tr.get("telegram_file_id") or tr.get("storage_channel_message_id") for tr in existing_translations if tr.get("language") == "O'zbekcha")
    if has_video:
        logger.info(
            f"[AUTO_INDEX DECISION] chat={message.chat.id} topic={message.message_thread_id} msg_id={message.message_id} "
            f"decision=SKIPPED_ALREADY_ATTACHED reason=movie id={movie.get('id')} already has O'zbekcha video translation (no overwrite)"
        )
        return

    # DRY-RUN TEKSHIRUVI: Agar AUTO_INDEX_DRY_RUN True bo'lsa, videoni saqlash va link qilish bajarilmaydi
    if getattr(settings, "AUTO_INDEX_DRY_RUN", True):
        logger.info(
            f"[AUTO_INDEX DRY-RUN DECISION] chat={message.chat.id} topic={message.message_thread_id} "
            f"msg_id={message.message_id} decision=DRY_RUN_WOULD_INDEX movie_id={movie.get('id')} "
            f"title='{movie.get('title')}' code={movie_code} reason=AUTO_INDEX_DRY_RUN is True (no backend writes)"
        )
        return

    # Copy video to storage channel with flood control retry
    try:
        storage_msg = await safe_copy_message_with_retry(
            bot=bot,
            chat_id=settings.STORAGE_CHANNEL_ID,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            caption=storage_caption,
            parse_mode="HTML",
            notify_msg=message,
            item_label="Kino",
            max_retries=5
        )
        storage_msg_id = storage_msg.message_id
    except Exception as e:
        logger.error(f"Cannot copy movie message to storage: {e}")
        try:
            await message.reply(f"❌ Videoni Storage kanalga ko'chirib bo'lmadi: {e}")
        except Exception as reply_err:
            logger.debug(f"Xabar yuborishda xatolik: {reply_err}")
        return

    # Link video to movie
    try:
        resp = await api_client.client.post(f"/movies/{movie['id']}/link-video", json={
            "message_id": storage_msg_id,
            "language": "O'zbekcha",
            "telegram_file_id": telegram_file_id
        })
        if resp.status_code == 409:
            logger.warning(
                f"[AUTO_INDEX DECISION] chat={message.chat.id} topic={message.message_thread_id} msg_id={message.message_id} "
                f"decision=REJECTED_OVERWRITE reason=movie {movie.get('id')} already has video or file attached to another title"
            )
            return
        resp.raise_for_status()
        await message.reply(f"✅ Kino videosi saqlandi va indekslandi. Kod: `{movie['code']}`", parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Error linking video for movie {movie['id']}: {e}")
        try:
            await message.reply(f"❌ Kino bazaga qo'shildi, lekin videoni ulashda xatolik yuz berdi: {e}")
        except Exception as reply_err:
            logger.debug(f"Xabar yuborishda xatolik: {reply_err}")


async def process_series_batch(messages: list[Message], bot: Bot, series: dict):
    storage_channel_id = settings.STORAGE_CHANNEL_ID
    if not storage_channel_id:
        logger.warning("STORAGE_CHANNEL_ID is not set.")
        for msg in messages:
            try:
                await msg.reply("❌ STORAGE_CHANNEL_ID sozlanmagan! Videoni saqlab bo'lmaydi.")
            except Exception as reply_err:
                logger.debug(f"Xabar yuborishda xatolik: {reply_err}")
        return

    # DRY-RUN TEKSHIRUVI: Agar AUTO_INDEX_DRY_RUN True bo'lsa, hech qanday mavsum/qism yaratilmaydi
    if getattr(settings, "AUTO_INDEX_DRY_RUN", True):
        for msg in messages:
            explicit_ep = extract_episode_num_from_caption(msg.caption)
            logger.info(
                f"[AUTO_INDEX DRY-RUN DECISION] chat={msg.chat.id} topic={msg.message_thread_id} "
                f"msg_id={msg.message_id} decision=DRY_RUN_WOULD_INDEX series_id={series.get('id')} "
                f"title='{series.get('title')}' ep={explicit_ep} reason=AUTO_INDEX_DRY_RUN is True (no backend writes)"
            )
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
                    except Exception as reply_err:
                        logger.debug(f"Xabar yuborishda xatolik: {reply_err}")
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
                    except Exception as reply_err:
                        logger.debug(f"Xabar yuborishda xatolik: {reply_err}")
                return

    season_id = season['id']

    # ── BOSQICH A — RESERVE (copy_message'dan OLDIN, hech qanday Telegram network chaqiruvisiz) ──
    reservation_items = []
    for msg in messages:
        explicit_ep = extract_episode_num_from_caption(msg.caption)
        t_file_id, _ = extract_media_info(msg)
        reservation_items.append({
            "source_message_id": msg.message_id,
            "explicit_episode_number": explicit_ep,
            "telegram_file_id": t_file_id,
            "title": f"{explicit_ep}-qism" if explicit_ep else None
        })

    recv_ts = time.time()
    reserved_episodes = await api_client.reserve_episodes(season_id, reservation_items)
    if not reserved_episodes:
        logger.error(f"Failed to reserve episodes for season {season_id}")
        for msg in messages:
            try:
                await msg.reply("❌ Qismlarni DB'da band qilishda tizimli xato yuz berdi.")
            except Exception as reply_err:
                logger.debug(f"Xabar yuborishda xatolik: {reply_err}")
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
                await safe_send_photo_with_retry(bot, storage_channel_id, photo=poster_url, caption=post_caption, parse_mode="Markdown")
            else:
                await safe_send_message_with_retry(bot, storage_channel_id, text=post_caption, parse_mode="Markdown")
            await asyncio.sleep(1.0)
        except Exception as e:
            logger.warning(f"Could not send series banner to storage: {e}")
    elif is_first_season_ep:
        season_title = season.get('title') or f"{season.get('season_number', 1)}-mavsum"
        try:
            await safe_send_message_with_retry(bot, storage_channel_id, text=f"📺 *{season_title}*", parse_mode="Markdown")
            await asyncio.sleep(1.0)
        except Exception as e:
            logger.warning(f"Could not send season banner to storage: {e}")

    # ── BOSQICH B — UPLOAD (endi xavfsiz parallel yoki ketma-ket, order bazada band) ──
    s_num = season.get('season_number', 1)
    series_title = html.escape(series.get('title') or '')

    for idx, msg in enumerate(messages):
        reserved_info = reserved_map.get(msg.message_id)
        if not reserved_info:
            continue

        # DUBLIKAT TEKSHIRUVI: Agar qayta forward qilingan xabar bo'lsa, yangi qism yaratmaymiz va qayta yuklamaymiz
        if reserved_info.get("is_duplicate"):
            logger.info(
                f"[AUTO_INDEX DECISION] chat={msg.chat.id} topic={msg.message_thread_id} msg_id={msg.message_id} "
                f"decision=SKIPPED_DUPLICATE reason=re-forwarded duplicate of episode {reserved_info.get('episode_number')} (code={reserved_info.get('display_code')})"
            )
            continue

        ep_num = reserved_info["episode_number"]
        ep_id = reserved_info["id"]
        ep_code = reserved_info["display_code"]
        is_update = reserved_info.get("is_update", False)

        telegram_file_id, _ = extract_media_info(msg)
        if not telegram_file_id:
            try:
                await msg.reply(f"❌ <b>{ep_num}-qism</b>: Yuborilgan fayl video emas.", parse_mode="HTML")
            except Exception as reply_err:
                logger.debug(f"Xabar yuborishda xatolik: {reply_err}")
            continue

        caption_lines = [
            f"🍿 <b>{series_title}</b>",
            f"📌 <b>{s_num}-mavsum, {ep_num}-qism</b>"
        ]
        if ep_code:
            caption_lines.append(f"🔑 <b>Qism kodi:</b> <code>{ep_code}</code>")
        if series.get("id"):
            caption_lines.append(f"📺 <b>Serial kodi:</b> <code>s_{series['id']}</code>")
        if series.get("release_year"):
            caption_lines.append(f"📅 <b>Yili:</b> {series['release_year']}")
        storage_caption = "\n".join(caption_lines)

        # Copy to storage channel with flood control retry
        try:
            copied = await safe_copy_message_with_retry(
                bot=bot,
                chat_id=storage_channel_id,
                from_chat_id=msg.chat.id,
                message_id=msg.message_id,
                caption=storage_caption,
                parse_mode="HTML",
                notify_msg=msg,
                item_label=f"{ep_num}-qism",
                max_retries=5
            )
            storage_msg_id = copied.message_id
        except Exception as e:
            logger.error(f"[ORDER_AUDIT] msg_id={msg.message_id} | status=FAILED | error={e}")
            try:
                await msg.reply(
                    f"⚠️ <b>{ep_num}-qism</b> bazada band qilindi ({ep_code}), lekin videoni Storage kanalga ko'chirishda xatolik: {e}",
                    parse_mode="HTML"
                )
            except Exception as reply_err:
                logger.debug(f"Xabar yuborishda xatolik: {reply_err}")
            continue

        # Link video to reserved episode
        try:
            resp = await api_client.client.post(f"/series/episodes/{ep_id}/link-video", json={
                "message_id": storage_msg_id,
                "language": "O'zbekcha",
                "telegram_file_id": telegram_file_id
            })
            if resp.status_code == 409:
                logger.warning(
                    f"[AUTO_INDEX DECISION] chat={msg.chat.id} topic={msg.message_thread_id} msg_id={msg.message_id} "
                    f"decision=REJECTED_OVERWRITE reason=episode {ep_num} already has video or file attached to another title"
                )
                continue
            resp.raise_for_status()
            logger.info(
                f"[ORDER_AUDIT] msg_id={msg.message_id} | "
                f"db_write_ts={time.time():.3f} | "
                f"final_ep={ep_num} | "
                f"code={ep_code} | "
                f"status=DB_COMMITTED"
            )
            if is_update:
                await msg.reply(
                    f"🔄 <b>{ep_num}-qism</b> videosi yangilandi.\n"
                    f"🔑 Qism kodi: <code>{ep_code}</code>\n"
                    f"📺 Serial kodi: <code>s_{series['id']}</code>",
                    parse_mode="HTML"
                )
            else:
                await msg.reply(
                    f"✅ <b>{ep_num}-qism</b> saqlandi va indekslandi.\n"
                    f"🔑 Qism kodi: <code>{ep_code}</code>\n"
                    f"📺 Serial kodi: <code>s_{series['id']}</code>",
                    parse_mode="HTML"
                )
                # Obunachilarga yangi qism chiqqani haqida bildirishnoma yuborish
                try:
                    await api_client.notify_new_episode(
                        series_id=series["id"],
                        season_number=s_num,
                        episode_number=ep_num,
                        display_code=ep_code
                    )
                except Exception as notify_err:
                    logger.warning(f"Failed to notify subscribers: {notify_err}")
        except Exception as e:
            logger.error(f"Error linking video for episode {ep_id}: {e}")
            try:
                await msg.reply(f"❌ <b>{ep_num}-qism</b> videosini ulashda xatolik yuz berdi: {e}", parse_mode="HTML")
            except Exception as reply_err:
                logger.debug(f"Xabar yuborishda xatolik: {reply_err}")

        # Throttle between consecutive copies to stay within Telegram rate limits (~20 msgs/min)
        if idx < len(messages) - 1:
            await asyncio.sleep(2.0)

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

    # Topic ID majburiy
    if topic_id is None:
        logger.info(
            f"[AUTO_INDEX DECISION] chat={chat_id} topic=None msg_id=N/A "
            f"decision=IGNORED reason=topic_id is None in flush_source_batch"
        )
        source_batches.pop(source_key, None)
        return

    # Allowlist tekshiruvi
    allowed_chats = getattr(settings, "AUTO_INDEX_ALLOWED_CHAT_IDS", []) or []
    if isinstance(allowed_chats, str):
        allowed_chats = [int(x.strip()) for x in allowed_chats.split(",") if x.strip()]
    if chat_id not in allowed_chats:
        logger.info(
            f"[AUTO_INDEX DECISION] chat={chat_id} topic={topic_id} msg_id=N/A "
            f"decision=IGNORED reason=chat_id not in AUTO_INDEX_ALLOWED_CHAT_IDS allowlist"
        )
        source_batches.pop(source_key, None)
        return

    # Kill switch tekshiruvi: agar AUTO_CONTENT_ENABLED o'chirilgan bo'lsa, xabarlar tashlab yuboriladi
    if not getattr(settings, "AUTO_CONTENT_ENABLED", False):
        logger.info(
            f"[AUTO_INDEX DECISION] chat={chat_id} topic={topic_id} msg_id=N/A "
            f"decision=IGNORED reason=AUTO_CONTENT_ENABLED is False (kill switch active)"
        )
        source_batches.pop(source_key, None)
        return

    # Protect batch saving with source-level lock
    lock = get_source_lock(chat_id, topic_id)
    async with lock:
        batch = source_batches.pop(source_key, None)
        if not batch or not batch.messages:
            return

        # 1. Telegram xabarlarini message_id bo'yicha o'sish tartibida saralash (1-qismdan boshlab)
        messages = sorted(batch.messages, key=lambda m: m.message_id)

        # 2. Source orqali Series yoki Movie qidirish
        url = f"/series/by-source?chat_id={chat_id}&topic_id={topic_id}"
        resp = await api_client.client.get(url)

        if resp.status_code == 409:
            for msg in messages:
                logger.warning(
                    f"[AUTO_INDEX DECISION] chat={chat_id} topic={topic_id} msg_id={msg.message_id} "
                    f"decision=REJECTED_AMBIGUOUS reason=topic maps to multiple entities or both movie and series"
                )
            return

        if resp.status_code == 404:
            # Movie tekshirish
            movie_url = f"/movies/by-source?chat_id={chat_id}&topic_id={topic_id}"
            resp_movie = await api_client.client.get(movie_url)
            if resp_movie.status_code == 409:
                for msg in messages:
                    logger.warning(
                        f"[AUTO_INDEX DECISION] chat={chat_id} topic={topic_id} msg_id={msg.message_id} "
                        f"decision=REJECTED_AMBIGUOUS reason=topic maps to multiple entities or both movie and series"
                    )
                return
            if resp_movie.status_code == 404:
                for msg in messages:
                    logger.info(
                        f"[AUTO_INDEX DECISION] chat={chat_id} topic={topic_id} msg_id={msg.message_id} "
                        f"decision=SKIPPED_NOT_FOUND reason=topic maps to zero entities in backend"
                    )
                return
            try:
                resp_movie.raise_for_status()
                movie = resp_movie.json()
            except Exception as e:
                logger.error(f"Error fetching movie by source: {e}")
                return

            for msg in messages:
                logger.info(
                    f"[AUTO_INDEX DECISION] chat={chat_id} topic={topic_id} msg_id={msg.message_id} "
                    f"decision=ROUTED_MOVIE reason=topic mapped to movie id={movie.get('id')}"
                )
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
                except Exception as reply_err:
                    logger.debug(f"Xabar yuborishda xatolik: {reply_err}")
            return

        # 3. Series uchun qismlarni ketma-ket indekslash
        for msg in messages:
            logger.info(
                f"[AUTO_INDEX DECISION] chat={chat_id} topic={topic_id} msg_id={msg.message_id} "
                f"decision=ROUTED_SERIES reason=topic mapped to series id={series.get('id')}"
            )
        await process_series_batch(messages, bot, series)


async def enqueue_video_message(message: Message, bot: Bot):
    chat_id = message.chat.id
    topic_id = message.message_thread_id

    # 1. KILL SWITCH: AUTO_CONTENT_ENABLED tekshiruvi (default False: hech narsa qabul qilinmaydi)
    if not getattr(settings, "AUTO_CONTENT_ENABLED", False):
        logger.info(
            f"[AUTO_INDEX DECISION] chat={chat_id} topic={topic_id} msg_id={message.message_id} "
            f"decision=IGNORED reason=AUTO_CONTENT_ENABLED is False (kill switch active)"
        )
        return

    # 2. ALLOWLIST: Faqat AUTO_INDEX_ALLOWED_CHAT_IDS ro'yxatidagi chat_id lar qabul qilinadi (default bo'sh = hech narsa olinmaydi)
    allowed_chats = getattr(settings, "AUTO_INDEX_ALLOWED_CHAT_IDS", []) or []
    if isinstance(allowed_chats, str):
        allowed_chats = [int(x.strip()) for x in allowed_chats.split(",") if x.strip()]
    if chat_id not in allowed_chats:
        logger.info(
            f"[AUTO_INDEX DECISION] chat={chat_id} topic={topic_id} msg_id={message.message_id} "
            f"decision=IGNORED reason=chat_id not in AUTO_INDEX_ALLOWED_CHAT_IDS allowlist"
        )
        return

    # 3. TOPIC_ID MAJBURIY: Faqat topic_id (message_thread_id) mavjud xabarlar qayta ishlanadi (mavzusiz = ignore)
    if topic_id is None:
        logger.info(
            f"[AUTO_INDEX DECISION] chat={chat_id} topic=None msg_id={message.message_id} "
            f"decision=IGNORED reason=message has no topic_id (message_thread_id is required)"
        )
        return

    source_key = f"{chat_id}:{topic_id}"
    logger.info(
        f"[AUTO_INDEX DECISION] chat={chat_id} topic={topic_id} msg_id={message.message_id} "
        f"decision=BUFFERED reason=message enqueued into source buffer"
    )

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
