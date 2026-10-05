"""
Telethon-based Moderator Pipeline for Kinochi Project.
Fully compatible with MTProto Layer 229, modern Telegram media formats,
and seamless interaction with @asilmediabot and @UzmovieTV_Bot.
"""

import os
import sys
import io
import re
import html
import time
import random
import asyncio
import logging
import sqlite3
from typing import Optional, Dict, Any, List

if sys.platform == "win32":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, "bot", ".env"))
if os.path.join(BASE_DIR, "backend") not in sys.path:
    sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from telethon import TelegramClient, utils
from telethon.sessions import MemorySession
from telethon.crypto import AuthKey
from telethon.tl.functions.messages import CreateForumTopicRequest
from telethon.tl.types import Message
from scraper.fast_telethon import fast_download, fast_upload

from scraper.config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    BOT_TOKEN,
    STORAGE_CHANNEL_ID,
    AUTO_TOPIC_CHAT_ID,
    TARGET_BOTS
)
from scraper.queue_manager import QueueItem
from scraper.duplicate_checker import DuplicateChecker
from scraper.smart_enricher import enrich_movie_smart, clean_movie_title

# Backend DB & Services
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.repositories.movie_repo import MovieRepositoryImpl
from app.application.movies.service import MovieService
from app.infrastructure.telegram.telegram_client import telegram_client
from app.infrastructure.db.repositories.series_repository import SeriesRepository
from app.application.series.series_service import SeriesService
from app.domain.series.entities import SeriesCreate, SeasonCreate, EpisodeCreate
from app.infrastructure.db.models.source import SourceModel
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.core.cache import delete_cache_pattern

logger = logging.getLogger(__name__)


def create_telethon_client(session_path: str = None) -> TelegramClient:
    session_file = session_path or os.path.join(BASE_DIR, "scraper", "kinochi_userbot.session")
    if not session_file.endswith(".session"):
        session_file += ".session"

    conn = sqlite3.connect(session_file)
    c = conn.cursor()
    c.execute("SELECT dc_id, auth_key FROM sessions")
    row = c.fetchone()
    conn.close()

    if not row:
        raise ValueError(f"Session faylidan ma'lumot olinmadi: {session_file}")

    dc_id, auth_key_bytes = row
    dc_ips = {
        1: "149.154.175.53",
        2: "149.154.167.51",
        4: "149.154.167.91",
    }
    session = MemorySession()
    session.set_dc(dc_id, dc_ips.get(dc_id, "149.154.167.51"), 443)
    session.auth_key = AuthKey(data=auth_key_bytes)

    return TelegramClient(session, TELEGRAM_API_ID, TELEGRAM_API_HASH)


async def poll_new_messages(
    client: TelegramClient,
    chat: str,
    after_id: int,
    timeout: float = 12.0,
    interval: float = 0.35,
    condition = None
) -> List[Message]:
    """
    Bot xabarlarini 0.35 soniyalik interval bilan tezkor kuzatadi.
    Bot javob bergan millisekundda darhol natijani qaytaradi (blind sleep yo'q).
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        await asyncio.sleep(interval)
        msgs = []
        async for m in client.iter_messages(chat, limit=8):
            if m.id > after_id:
                msgs.append(m)
        if msgs:
            if condition is None or condition(msgs):
                return msgs
    return []


class TelethonModeratorPipeline:
    def __init__(self, client: TelegramClient, duplicate_checker: DuplicateChecker):
        self.client = client
        self.dup_checker = duplicate_checker
        self._last_card_msg: Optional[Message] = None

    async def run_item(self, item: QueueItem, target_bot: str = "asilmediabot") -> bool:
        """Kino yoki Serial turiga qarab mos pipeline siklini ishga tushiradi."""
        if item.media_type == "series":
            return await self.run_single_series(item=item, target_bot=target_bot)
        return await self.run_single_movie(item=item, target_bot=target_bot)

    async def run_single_series(self, item: QueueItem, target_bot: str = "asilmediabot") -> bool:
        logger.info("\n" + "="*55)
        logger.info(f"📺 SERIAL MODERATOR SIKLI: '{item.title}' ({item.year or 'Noma\'lum'}) | BOT: @{target_bot}")
        logger.info("="*55)

        clean_query = item.title.split('/')[0].split('|')[0].strip()
        clean_query = re.sub(r'\(.*?\)', '', clean_query).strip()
        clean_query = re.sub(r'^\d+\s+', '', clean_query).strip()
        clean_query = clean_movie_title(clean_query)

        # 1. Dublikat tekshiruvi (bazada bormi?)
        dup_check = await self.dup_checker.check(
            title=clean_query or item.title,
            year=item.year,
            original_title=item.original_title,
            media_type="series"
        )
        existing_series_id = None
        if dup_check.is_duplicate:
            logger.info(
                f"ℹ️ Serial bazada mavjud: ID={dup_check.matched_id} ('{dup_check.matched_title}'). "
                f"Yangi qismlar tekshiriladi..."
            )
            existing_series_id = dup_check.matched_id

        # 2. Botdan serial kartasi va qismlar menyusini topish
        is_uzmovie = "uzmovie" in target_bot.lower()
        is_asilmedia = "asilmedia" in target_bot.lower()
        search_query = clean_query
        num_match = re.search(r'\d+', item.id)
        if is_uzmovie and num_match and len(num_match.group(0)) <= 6:
            search_query = num_match.group(0)
        elif is_asilmedia and num_match and len(num_match.group(0)) <= 6:
            search_query = f"/start {num_match.group(0)}"

        logger.info(f"[@{target_bot}] botiga serial bo'yicha so'rov: '{search_query}'...")
        sent = await self.client.send_message(target_bot, search_query)

        # Tezkor reaktiv poller (0.35s)
        recent_msgs = await poll_new_messages(
            self.client,
            target_bot,
            sent.id,
            timeout=8.0,
            condition=lambda msgs: any(m.buttons for m in msgs)
        )

        card_msg = None
        for m in recent_msgs:
            if not m.buttons:
                continue

            # Agar qidiruv ro'yxati chiqsa
            if "topildi" in (m.text or "").lower():
                best_btn = None
                target_year_str = str(item.year) if item.year else ""
                for row_idx, row in enumerate(m.buttons):
                    for col_idx, btn in enumerate(row):
                        b_text = btn.text.lower()
                        if target_year_str and target_year_str in b_text:
                            best_btn = (row_idx, col_idx, btn.text)
                            break
                        if clean_query.lower() in b_text:
                            best_btn = (row_idx, col_idx, btn.text)
                    if best_btn:
                        break

                if not best_btn and m.buttons and m.buttons[0]:
                    best_btn = (0, 0, m.buttons[0][0].text)

                if best_btn:
                    r_idx, c_idx, b_name = best_btn
                    logger.info(f"Qidiruvdan serial tanlanmoqda: '{b_name}'...")
                    click_id = m.id
                    await m.click(r_idx, c_idx)

                    # Qismlar menyusi chiqishini tezkor kutish
                    def has_episodes(msgs):
                        return any(nm.buttons and any(b for row in nm.buttons for b in row if b.text.strip().isdigit() or "qism" in b.text.lower()) for nm in msgs)

                    nm_list = await poll_new_messages(self.client, target_bot, click_id, timeout=8.0, condition=has_episodes)
                    for nm in nm_list:
                        if nm.buttons and any(b for row in nm.buttons for b in row if b.text.strip().isdigit() or "qism" in b.text.lower()):
                            card_msg = nm
                            break
                break

            if any(b for row in m.buttons for b in row if b.text.strip().isdigit() or "qism" in b.text.lower()):
                card_msg = m
                break

        if not card_msg or not card_msg.buttons:
            async for nm in self.client.iter_messages(target_bot, limit=3):
                if nm.buttons and any(b for row in nm.buttons for b in row if b.text.strip().isdigit() or "qism" in b.text.lower()):
                    card_msg = nm
                    break

        if not card_msg or not card_msg.buttons:
            logger.warning(f"[@{target_bot}] Serial qismlari tugmalari topilmadi!")
            return False

        # Qismlar tugmalarini yig'ish
        episodes_map = {}  # ep_num -> (r_idx, c_idx, btn_text)
        for r_idx, row in enumerate(card_msg.buttons):
            for c_idx, btn in enumerate(row):
                t = btn.text.strip()
                if t.isdigit():
                    episodes_map[int(t)] = (r_idx, c_idx, t)
                else:
                    m_num = re.search(r'(\d+)\s*[-_]?\s*qism', t, re.I)
                    if m_num:
                        episodes_map[int(m_num.group(1))] = (r_idx, c_idx, t)

        if not episodes_map:
            logger.warning("Serialda raqamlangan qism tugmalari topilmadi!")
            return False

        logger.info(f"🎬 Botda {len(episodes_map)} ta qism topildi: {sorted(list(episodes_map.keys()))}")

        # 3. Serial ma'lumotlarini AI + TMDb orqali boyitish
        caption = card_msg.text or ""
        meta = await enrich_movie_smart(
            raw_title=clean_query or item.title,
            year=item.year,
            source_poster=item.poster_url,
            caption=caption,
            media_type="series"
        )
        title = meta["title"]
        year = meta["release_year"] or item.year
        year_str = f" ({year})" if year else ""

        # 4. Bazada serial va Forum Topic yaratish (agar yo'q bo'lsa)
        series_id = existing_series_id
        season_id = None
        thread_id = None
        target_chat = AUTO_TOPIC_CHAT_ID

        async with async_session_factory() as session:
            series_repo = SeriesRepository(session)
            series_service = SeriesService(repository=series_repo, telegram_api=telegram_client)

            if series_id:
                db_series = await series_service.get_series_by_id(series_id)
                if db_series:
                    if db_series.source and db_series.source.topic_id:
                        thread_id = db_series.source.topic_id
                    if db_series.seasons:
                        season_id = db_series.seasons[0].id

                if not season_id and series_id:
                    created_season = await series_service.create_season(SeasonCreate(
                        series_id=series_id,
                        season_number=1,
                        title="1-Mavsum"
                    ))
                    season_id = created_season.id
                    await session.commit()

                if not thread_id:
                    topic_name = f"🎬 {title} (Serial){year_str}"
                    logger.info(f"ℹ️ Mavjud serial uchun Forum Topic ochilmoqda: '{topic_name}'...")
                    thread_id = await self._create_topic(chat_id=target_chat, title=topic_name)
                    if thread_id and db_series and db_series.source_id:
                        src = await session.get(SourceModel, db_series.source_id)
                        if src:
                            src.topic_id = thread_id
                            await session.commit()

            if not series_id:
                topic_name = f"🎬 {title} (Serial){year_str}"
                logger.info(f"ℹ️ Forum Topic ochilmoqda: '{topic_name}'...")
                thread_id = await self._create_topic(chat_id=target_chat, title=topic_name)
                if not thread_id:
                    logger.error("Serial uchun Topic ochib bo'lmadi!")
                    return False
                logger.info(f"✅ Topic ochildi! Thread ID: {thread_id}")

                # Banner xabarini Topic ichiga yuborish
                rating_str = f"⭐ <b>IMDb:</b> {meta['imdb_rating']}/10\n" if meta.get("imdb_rating") else ""
                director_str = f"🎬 <b>Rejissyor:</b> {html.escape(meta['director'])}\n" if meta.get("director") else ""
                cast_str = f"👥 <b>Aktyorlar:</b> {html.escape(meta['cast'][:120])}...\n" if meta.get("cast") else ""
                trailer_str = f"🍿 <b>Treyler:</b> <a href=\"{meta['trailer_url']}\">YouTube</a>\n" if meta.get("trailer_url") else ""

                welcome_text = (
                    f"🎬 <b>{html.escape(title)}</b> (Serial){year_str}\n"
                    f"🎭 <b>Janr:</b> {html.escape(meta.get('genres') or 'Serial')}\n"
                    f"{rating_str}{director_str}{cast_str}{trailer_str}"
                    f"\n📝 <b>Tavsif:</b>\n<i>{html.escape(meta.get('description') or '')}</i>\n\n"
                    f"⬇️ <i>Serial qismlari shu yerga yuklanmoqda...</i>"
                )

                if meta.get("poster_url"):
                    try:
                        await self.client.send_file(
                            target_chat,
                            file=meta["poster_url"],
                            caption=welcome_text,
                            reply_to=thread_id,
                            parse_mode="html"
                        )
                    except Exception:
                        await self.client.send_message(target_chat, message=welcome_text, reply_to=thread_id, parse_mode="html")
                else:
                    await self.client.send_message(target_chat, message=welcome_text, reply_to=thread_id, parse_mode="html")

                # Source yaratish
                source = SourceModel(
                    name=title,
                    type="superguruh",
                    chat_id=int(target_chat),
                    topic_id=int(thread_id)
                )
                session.add(source)
                await session.flush()

                # Series yaratish
                series_data = SeriesCreate(
                    title=title,
                    description=meta.get("description"),
                    poster_url=meta.get("poster_url"),
                    trailer_url=meta.get("trailer_url"),
                    imdb_rating=meta.get("imdb_rating"),
                    tmdb_id=meta.get("tmdb_id"),
                    release_year=year,
                    director=meta.get("director"),
                    cast=meta.get("cast"),
                    category_ids=meta.get("category_ids"),
                    source_id=source.id,
                    status="ongoing"
                )
                created_series = await series_service.create_series(series_data)
                series_id = created_series.id

                # Season 1 yaratish
                created_season = await series_service.create_season(SeasonCreate(
                    series_id=series_id,
                    season_number=1,
                    title="1-Mavsum"
                ))
                season_id = created_season.id
                await session.commit()
                logger.info(f"✅ Serial bazada muvaffaqiyatli yaratildi (Series ID: {series_id}, Season ID: {season_id})")

        # 5. Mavjud qismlarni aniqlash (qayta yuklamaslik uchun)
        existing_eps = set()
        async with async_session_factory() as session:
            series_repo = SeriesRepository(session)
            s_model = await series_repo.get_season_by_id(season_id)
            if s_model and s_model.episodes:
                for ep in s_model.episodes:
                    if ep.translations:
                        existing_eps.add(ep.episode_number)

        # 6. Har bir qismni ketma-ket yuklash
        total_episodes = len(episodes_map)
        uploaded_count = 0
        storage_chat = STORAGE_CHANNEL_ID

        for ep_num in sorted(episodes_map.keys()):
            if ep_num in existing_eps:
                logger.info(f"⏭ {ep_num}-qism allaqachon mavjud, o'tkazib yuborildi.")
                continue

            r_idx, c_idx, btn_name = episodes_map[ep_num]
            logger.info(f"\n--- 📺 {ep_num}-qism yuklanmoqda ({btn_name}) [{uploaded_count + 1}/{total_episodes}] ---")

            try:
                # Bot tugmasini bosish
                click_id = card_msg.id
                await card_msg.click(r_idx, c_idx)

                # Video yoki sifat menyusini tezkor poller bilan kutish (0.35s)
                def is_ep_or_quality(msgs):
                    for nm in msgs:
                        if nm.file and nm.file.name and nm.file.name.lower().endswith(('.mp4', '.mkv', '.avi')):
                            return True
                        if nm.buttons and any(b for row in nm.buttons for b in row if any(q in b.text.lower() for q in ["720", "1080", "480"])):
                            return True
                    return False

                ep_reply_msgs = await poll_new_messages(self.client, target_bot, click_id, timeout=8.0, interval=0.35, condition=is_ep_or_quality)
                ep_video_msg = None
                quality_msg = None

                for nm in ep_reply_msgs:
                    if nm.file and nm.file.name and nm.file.name.lower().endswith(('.mp4', '.mkv', '.avi')):
                        f_lower = (nm.file.name or "").lower()
                        t_lower = (nm.text or "").lower()
                        if f"{ep_num}-qism" in f_lower or f"{ep_num}-qism" in t_lower or f"{ep_num} qism" in t_lower or total_episodes == 1:
                            ep_video_msg = nm
                            break
                    if nm.buttons and any(b for row in nm.buttons for b in row if any(q in b.text.lower() for q in ["720", "1080", "480"])):
                        quality_msg = nm
                        break

                # Agar sifat menyusi chiqqan bo'lsa
                if quality_msg and not ep_video_msg:
                    q_btns = {}
                    for q_r, q_row in enumerate(quality_msg.buttons):
                        for q_c, q_b in enumerate(q_row):
                            t = q_b.text.lower()
                            if "720" in t:
                                q_btns["720p"] = (q_r, q_c, q_b.text)
                            elif "1080" in t:
                                q_btns["1080p"] = (q_r, q_c, q_b.text)
                            elif "480" in t:
                                q_btns["480p"] = (q_r, q_c, q_b.text)
                    chosen_q = q_btns.get("720p") or q_btns.get("1080p") or q_btns.get("480p")
                    if chosen_q:
                        q_r, q_c, q_name = chosen_q
                        logger.info(f"Sifat tugmasi tanlanmoqda: '{q_name}'...")
                        q_click_id = quality_msg.id
                        await quality_msg.click(q_r, q_c)

                        def has_final_video(msgs):
                            return any(vm.file and vm.file.name and vm.file.name.lower().endswith(('.mp4', '.mkv', '.avi')) for vm in msgs)

                        v_list = await poll_new_messages(self.client, target_bot, q_click_id, timeout=18.0, interval=0.4, condition=has_final_video)
                        for vm in v_list:
                            if vm.file and vm.file.name and vm.file.name.lower().endswith(('.mp4', '.mkv', '.avi')):
                                ep_video_msg = vm
                                break

                # Fallback: oxirgi xabarlardan shu qism videosini tekshirish
                if not ep_video_msg:
                    async for fallback_m in self.client.iter_messages(target_bot, limit=10):
                        if fallback_m.file and fallback_m.file.name and fallback_m.file.name.lower().endswith(('.mp4', '.mkv', '.avi')):
                            f_name_lower = (fallback_m.file.name or "").lower()
                            f_text_lower = (fallback_m.text or "").lower()
                            if f"{ep_num}-qism" in f_name_lower or f"{ep_num}-qism" in f_text_lower or f"{ep_num} qism" in f_text_lower or total_episodes == 1:
                                ep_video_msg = fallback_m
                                logger.info(f"ℹ️ Zaxiradagi xabarlardan {ep_num}-qism videosi topildi (Msg ID: {ep_video_msg.id})")
                                break

                if not ep_video_msg:
                    logger.warning(f"❌ {ep_num}-qism videosi botdan qabul qilinmadi!")
                    continue

                # Topic ichiga yuklash
                ep_caption = (
                    f"🎬 <b>{html.escape(title)}</b>\n"
                    f"🔢 <b>1-Mavsum, {ep_num}-Qism</b>"
                )
                topic_msg = await self._upload_video_to_chat(
                    video_msg=ep_video_msg,
                    target_chat=target_chat,
                    reply_to=thread_id,
                    caption=ep_caption
                )
                if not topic_msg:
                    logger.error(f"❌ {ep_num}-qism Topicga yuklanmadi!")
                    continue

                # Storage kanalga server-side nusxalash
                storage_caption = (
                    f"🎬 <b>{html.escape(title)}</b>\n"
                    f"🔢 <b>1-Mavsum, {ep_num}-Qism</b>\n"
                    + (f"📅 <b>Yili:</b> {year}\n" if year else "")
                )
                storage_msg = await self._upload_video_to_chat(
                    video_msg=topic_msg,
                    target_chat=storage_chat,
                    reply_to=None,
                    caption=storage_caption
                )
                if not storage_msg:
                    logger.error(f"❌ {ep_num}-qism Storage kanalga nusxalanmadi!")
                    continue

                # Bazada Episode yaratish va bog'lash
                async with async_session_factory() as session:
                    series_repo = SeriesRepository(session)
                    series_service = SeriesService(repository=series_repo, telegram_api=telegram_client)

                    ep_entity = await series_service.create_episode(EpisodeCreate(
                        season_id=season_id,
                        episode_number=ep_num,
                        title=f"{ep_num}-qism"
                    ))
                    ep_id = ep_entity.id

                    ep_bot_file_id = None
                    try:
                        from telethon.utils import pack_bot_file_id
                        if storage_msg and storage_msg.media:
                            ep_bot_file_id = pack_bot_file_id(storage_msg.media)
                    except Exception:
                        pass

                    await series_repo.add_episode_translation(
                        episode_id=ep_id,
                        language="Asosiy",
                        telegram_file_id=ep_bot_file_id,
                        storage_channel_message_id=storage_msg.id
                    )
                    await session.commit()

                try:
                    await delete_cache_pattern("cache:series:*")
                except Exception:
                    pass

                uploaded_count += 1
                logger.info(f"✅ {ep_num}-qism to'liq yuklandi va bazaga bog'landi! (Storage Msg: {storage_msg.id})")

                # Telegram FloodWait dan saqlanish uchun xavfsiz qisqa tanaffus
                await asyncio.sleep(1.0)

            except Exception as ep_err:
                logger.error(f"❌ {ep_num}-qismni yuklashda xatolik: {ep_err}")
                await asyncio.sleep(2.0)

        logger.info(f"\n🎉 Serial yakunlandi: {title} | {uploaded_count} ta yangi qism yuklandi.")
        return uploaded_count > 0

    async def run_single_movie(self, item: QueueItem, target_bot: str = "asilmediabot") -> bool:
        logger.info("\n" + "="*55)
        logger.info(f"🎬 MODERATOR SIKLI: '{item.title}' ({item.year or 'Noma\'lum'}) | BOT: @{target_bot}")
        logger.info("="*55)

        # 1. Dublikat tekshiruvi
        dup_check = await self.dup_checker.check(
            title=item.title,
            year=item.year,
            original_title=item.original_title,
            media_type=item.media_type
        )
        if dup_check.is_duplicate:
            logger.warning(
                f"⚠️ [DUBLIKAT] '{item.title}' bazada mavjud: "
                f"[{dup_check.matched_type}] '{dup_check.matched_title}' "
                f"(ID: {dup_check.matched_id}, Kod: {dup_check.matched_code}). O'tkazib yuborildi."
            )
            QueueManager().update_status(
                item.id,
                "already_exists",
                error_message=f"Bazada mavjud: {dup_check.reason} (ID: {dup_check.matched_id})"
            )
            return False

        # 2. Botdan video olish (video_msg va card_msg olinadi)
        video_msg = await self._fetch_video(item=item, target_bot=target_bot)
        if not video_msg:
            logger.warning(f"❌ '{item.title}' bo'yicha @{target_bot} dan video olinmadi.")
            return False

        return await self._process_pipeline(item=item, video_msg=video_msg, target_bot=target_bot, card_msg=self._last_card_msg)

    async def run_by_code(self, code: str, target_bot: str = "asilmediabot") -> bool:
        logger.info("\n" + "="*55)
        logger.info(f"🎬 MODERATOR SIKLI: KOD #{code} | BOT: @{target_bot}")
        logger.info("="*55)

        video_msg = await self._fetch_video(code=code, target_bot=target_bot)
        if not video_msg:
            logger.warning(f"❌ Kod #{code} bo'yicha botdan video olinmadi.")
            return False

        caption = video_msg.text or ""
        caption_title_m = re.search(r'🎬\s*([^\n\r–]+)', caption)
        raw_title = caption_title_m.group(1).strip() if caption_title_m else f"Film #{code}"
        raw_title = clean_movie_title(raw_title)

        caption_year = None
        year_m = re.search(r'Yil:\s*(\d{4})', caption, re.I)
        if year_m:
            caption_year = int(year_m.group(1))
        else:
            year_fallback = re.search(r'\b(19\d{2}|20\d{2})\b', caption)
            if year_fallback:
                caption_year = int(year_fallback.group(1))

        item = QueueItem(
            id=f"{target_bot.lower()}_{code}",
            source="asilmedia" if "asil" in target_bot.lower() else "uzmovi",
            title=raw_title,
            year=caption_year,
            media_type="movie"
        )

        return await self._process_pipeline(item=item, video_msg=video_msg, target_bot=target_bot, card_msg=self._last_card_msg)

    async def _process_pipeline(
        self,
        item: QueueItem,
        video_msg: Message,
        target_bot: str,
        card_msg: Optional[Message] = None
    ) -> bool:
        card_text = card_msg.text if (card_msg and card_msg.text) else ""
        full_context_caption = card_text or video_msg.text or ""

        caption_title_m = re.search(r'🎬\s*([^\n\r–]+)', full_context_caption)
        caption_title = clean_movie_title(caption_title_m.group(1)) if caption_title_m else clean_movie_title(item.title)

        caption_year = item.year
        year_m = re.search(r'Yil:\s*(\d{4})', full_context_caption, re.I)
        if year_m:
            caption_year = int(year_m.group(1))
        elif not caption_year:
            year_fallback = re.search(r'\b(19\d{2}|20\d{2})\b', full_context_caption)
            if year_fallback:
                caption_year = int(year_fallback.group(1))

        # Dublikat tekshiruvi (video sarlavhasi bo'yicha)
        dup_check = await self.dup_checker.check(
            title=caption_title or item.title,
            year=caption_year,
            original_title=item.original_title,
            media_type=item.media_type
        )
        if dup_check.is_duplicate:
            logger.warning(
                f"⚠️ [DUBLIKAT] '{caption_title}' bazada mavjud: "
                f"[{dup_check.matched_type}] '{dup_check.matched_title}' "
                f"(ID: {dup_check.matched_id}, Kod: {dup_check.matched_code}). O'tkazib yuborildi."
            )
            QueueManager().update_status(
                item.id,
                "already_exists",
                error_message=f"Bazada mavjud: {dup_check.reason} (ID: {dup_check.matched_id})"
            )
            return False

        # ── 1. AI + TMDb boyitish (To'liq bot konteksti bilan) ──
        logger.info("ℹ️ 1-QADAM: Kino ma'lumotlari AI (Gemini) + TMDb orqali shakllantirilmoqda...")
        meta = await enrich_movie_smart(
            raw_title=caption_title or item.title,
            year=caption_year,
            source_poster=item.poster_url,
            source_desc=card_text or None,
            caption=full_context_caption,
            item_url=item.url
        )

        title = meta["title"]
        year = meta["release_year"]
        year_str = f" ({year})" if year else ""

        # ── 2. PostgreSQL bazasida kino yaratish ──
        logger.info(f"ℹ️ 2-QADAM: Websayt bazasiga yangi kino qo'shilmoqda: '{title}'...")
        async with async_session_factory() as session:
            repo = MovieRepositoryImpl(session)
            service = MovieService(repo)
            created_movie = await service.create_movie(
                title=title,
                original_title=meta.get("original_title"),
                description=meta.get("description"),
                imdb_rating=meta.get("imdb_rating"),
                tmdb_rating=meta.get("tmdb_rating"),
                tmdb_id=meta.get("tmdb_id"),
                genres=meta.get("genres"),
                cast=meta.get("cast"),
                director=meta.get("director"),
                release_year=year,
                runtime=meta.get("runtime"),
                poster_url=meta.get("poster_url"),
                trailer_url=meta.get("trailer_url"),
                category_ids=meta.get("category_ids")
            )
            movie_id = created_movie.id
            movie_code = created_movie.code
            await session.commit()
            logger.info(f"✅ Websayt bazasida yaratildi! ID: {movie_id} | Unikal Kod: #{movie_code}")

        # ── 3. 'manba' superguruhida Topic ochish ──
        target_chat = AUTO_TOPIC_CHAT_ID
        topic_name = f"🎬 {title}{year_str}"
        logger.info(f"ℹ️ 3-QADAM: Guruhda Forum Topic ochilmoqda: '{topic_name}'...")
        thread_id = await self._create_topic(chat_id=target_chat, title=topic_name)
        if not thread_id:
            logger.error("Topic ochib bo'lmadi!")
            return False
        logger.info(f"✅ Topic muvaffaqiyatli ochildi! Thread ID: {thread_id}")

        # Kirish bannerini Topicga yuborish
        rating_str = f"⭐ <b>IMDb:</b> {meta['imdb_rating']}/10\n" if meta.get("imdb_rating") else ""
        director_str = f"🎬 <b>Rejissyor:</b> {html.escape(meta['director'])}\n" if meta.get("director") else ""
        cast_str = f"👥 <b>Aktyorlar:</b> {html.escape(meta['cast'][:120])}...\n" if meta.get("cast") else ""
        trailer_str = f"🍿 <b>Treyler:</b> <a href=\"{meta['trailer_url']}\">YouTube</a>\n" if meta.get("trailer_url") else ""

        welcome_text = (
            f"🎬 <b>{html.escape(title)}</b>{year_str}\n"
            f"🔑 <b>Film kodi:</b> <code>{movie_code}</code>\n"
            f"🎭 <b>Janr:</b> {html.escape(meta.get('genres') or 'Tarjima kino')}\n"
            f"{rating_str}{director_str}{cast_str}{trailer_str}"
            f"\n📝 <b>Tavsif:</b>\n<i>{html.escape(meta['description'][:400])}...</i>\n\n"
            f"⬇️ <i>Kino videosi shu yerga yuklanmoqda...</i>"
        )
        try:
            if meta.get("poster_url"):
                try:
                    await self.client.send_file(
                        target_chat,
                        file=meta["poster_url"],
                        caption=welcome_text,
                        reply_to=thread_id,
                        parse_mode="html"
                    )
                except Exception:
                    await self.client.send_message(
                        target_chat,
                        message=welcome_text,
                        reply_to=thread_id,
                        parse_mode="html"
                    )
            else:
                await self.client.send_message(
                    target_chat,
                    message=welcome_text,
                    reply_to=thread_id,
                    parse_mode="html"
                )
        except Exception as e:
            logger.warning(f"Kirish postini yuborishda xatolik: {e}")

        # Bazada movie manbasini (source_chat_id, source_topic_id) bog'lash
        async with async_session_factory() as session:
            repo = MovieRepositoryImpl(session)
            service = MovieService(repo)
            await service.update_movie(
                movie_id=movie_id,
                source_chat_id=int(target_chat),
                source_topic_id=thread_id
            )
            await session.commit()
            logger.info(f"✅ Kino bazada ochilgan Topic (Thread ID: {thread_id}) ga bog'landi.")

        # ── 4. Videoni Topic ichiga ko'chirish / yuklash ──
        logger.info(f"ℹ️ 4-QADAM: Video Topic (ID: {thread_id}) ga ko'chirilmoqda...")
        clean_caption = f"🍿 <b>{title}</b>{year_str}\n🔑 <b>Kod:</b> <code>{movie_code}</code>"

        topic_video_msg = await self._upload_video_to_chat(
            video_msg=video_msg,
            target_chat=target_chat,
            reply_to=thread_id,
            caption=clean_caption
        )
        if not topic_video_msg:
            logger.error("Videoni Topic ichiga yuklab bo'lmadi!")
            return False
        logger.info(f"✅ Video Topic ichiga muvaffaqiyatli joylashtirildi! (Message ID: {topic_video_msg.id})")

        # ── 5. Private Storage kanalga ko'chirish va Websaytga ulash ──
        logger.info(f"ℹ️ 5-QADAM: Video Private Storage kanalga saqlanmoqda va Websaytga ulanmoqda...")
        storage_chat = STORAGE_CHANNEL_ID
        storage_caption = (
            f"🍿 <b>{html.escape(title)}</b>\n"
            f"🔑 <b>Kodi:</b> <code>{movie_code}</code>\n"
            + (f"📅 <b>Yili:</b> {year}\n" if year else "")
        )

        storage_msg = await self._upload_video_to_chat(
            video_msg=topic_video_msg,
            target_chat=storage_chat,
            reply_to=None,
            caption=storage_caption
        )
        if not storage_msg:
            logger.warning("Storage kanalga ko'chirishda xatolik yuz berdi, lekin video Topicda bor.")
            return True

        # Video faylni websayt bazasiga ulash
        bot_file_id = None
        try:
            from telethon.utils import pack_bot_file_id
            if storage_msg and storage_msg.media:
                bot_file_id = pack_bot_file_id(storage_msg.media)
        except Exception as e:
            logger.warning(f"Could not pack bot file id: {e}")

        async with async_session_factory() as session:
            repo = MovieRepositoryImpl(session)
            service = MovieService(repo)
            await service.link_movie_video_from_message(
                movie_id=movie_id,
                message_id=storage_msg.id,
                language="Asosiy",
                telegram_file_id=bot_file_id
            )
            await session.commit()
            logger.info(f"🎉 WEBSAYTDA VIDEO TO'LIQ FAOLLASHTIRILDI! Onlayn tomosha qilishga tayyor! (Kod: #{movie_code})")

        # Keshni tozalash
        try:
            from app.core.cache import delete_cache_pattern
            await delete_cache_pattern("cache:movies:*")
        except Exception:
            pass

        # Topic ichiga tasdiqlash xabari
        confirm_text = (
            f"✅ <b>Kino videosi saqlandi va indekslandi.</b>\n"
            f"🔑 Kod: <code>{movie_code}</code>\n"
            f"🌐 Websaytda onlayn tomosha qilishga tayyor!"
        )
        try:
            await self.client.send_message(
                target_chat,
                message=confirm_text,
                reply_to=thread_id,
                parse_mode="html"
            )
        except Exception:
            pass

        return True

    async def _create_topic(self, chat_id: int, title: str) -> Optional[int]:
        try:
            peer = await self.client.get_input_entity(chat_id)
            r_id = random.randint(1, 2**31 - 1)
            res = await self.client(CreateForumTopicRequest(
                peer=peer,
                title=title[:128],
                random_id=r_id
            ))
            topic_id = None
            for u in getattr(res, 'updates', []):
                if hasattr(u, 'message') and hasattr(u.message, 'id'):
                    topic_id = u.message.id
                    break
                elif hasattr(u, 'id'):
                    topic_id = u.id
            return topic_id
        except Exception as e:
            logger.error(f"Topic ochishda xatolik: {e}")
            return None

    async def _fetch_video(
        self,
        item: Optional[QueueItem] = None,
        target_bot: str = "asilmediabot",
        code: Optional[str] = None
    ) -> Optional[Message]:
        self._last_card_msg = None
        is_uzmovie = "uzmovie" in target_bot.lower()

        search_query = ""
        if code:
            search_query = str(code).strip()
        elif item:
            num_match = re.search(r'\d+', item.id)
            if num_match and len(num_match.group(0)) <= 6:
                search_query = num_match.group(0)
            else:
                clean_name = item.title.split('/')[0].split('|')[0].strip()
                clean_name = re.sub(r'\(.*?\)', '', clean_name).strip()
                clean_name = re.sub(r'^\d+\s+', '', clean_name).strip()
                search_query = clean_name

        if not search_query:
            logger.warning("Botga yuborish uchun so'rov topilmadi!")
            return None

        if not is_uzmovie:
            return await self._fetch_asilmedia_video(query=search_query, year=item.year if item else None)

        # UzmovieTV_Bot flow
        logger.info(f"[{target_bot}] botiga so'rov yuborilmoqda: '{search_query}'...")
        sent = await self.client.send_message(target_bot, search_query)
        def has_uzmovie_file(msgs):
            return any(m.file for m in msgs)
        recent = await poll_new_messages(self.client, target_bot, sent.id, timeout=10.0, condition=has_uzmovie_file)
        for m in recent:
            if m.file:
                return m

        return None

    async def _fetch_asilmedia_video(
        self,
        query: str,
        year: Optional[int] = None,
        max_file_size_mb: float = 1980.0
    ) -> Optional[Message]:
        bot = "asilmediabot"
        clean_query = query.split('/')[0].split('|')[0].strip()
        clean_query = re.sub(r'\(.*?\)', '', clean_query).strip()
        clean_query = re.sub(r'^\d+\s+', '', clean_query).strip()

        if clean_query.isdigit():
            msg_to_send = f"/start {clean_query}"
        else:
            msg_to_send = clean_query

        logger.info(f"[@{bot}] ga so'rov yuborilmoqda: '{msg_to_send}'...")
        sent = await self.client.send_message(bot, msg_to_send)

        # 0.35s tezkor poller orqali kutamiz (3.5s qotib turish yo'q)
        recent_msgs = await poll_new_messages(self.client, bot, sent.id, timeout=8.0)

        if not recent_msgs:
            logger.warning(f"[@{bot}] dan javob kelmadi: '{clean_query}'")
            return None

        # 1. To'g'ridan-to'g'ri video
        for m in recent_msgs:
            if m.file and m.file.name and m.file.name.endswith(('.mp4', '.mkv', '.avi')):
                logger.info(f"To'g'ridan-to'g'ri video topildi: {m.file.name} ({round(m.file.size/1024/1024, 1)}MB)")
                return m

        # 2. Qidiruv ro'yxati (Search results) yoki Film kartasi
        card_msg = None
        for m in recent_msgs:
            if not m.buttons:
                continue

            if "topildi" in (m.text or "").lower():
                best_btn = None
                target_year_str = str(year) if year else ""
                for row_idx, row in enumerate(m.buttons):
                    for col_idx, btn in enumerate(row):
                        b_text = btn.text.lower()
                        if target_year_str and target_year_str in b_text:
                            best_btn = (row_idx, col_idx, btn.text)
                            break
                        if clean_query.lower() in b_text:
                            best_btn = (row_idx, col_idx, btn.text)
                    if best_btn:
                        break

                if not best_btn and m.buttons and m.buttons[0]:
                    best_btn = (0, 0, m.buttons[0][0].text)

                if best_btn:
                    r_idx, c_idx, b_name = best_btn
                    logger.info(f"Qidiruv natijasidan film tanlanmoqda: '{b_name}'...")
                    click_id = m.id
                    await m.click(r_idx, c_idx)
                    def has_card(msgs):
                        return any(nm.buttons and any(b for row in nm.buttons for b in row if any(q in b.text for q in ["1080", "720", "480"])) for nm in msgs)
                    nm_list = await poll_new_messages(self.client, bot, click_id, timeout=8.0, condition=has_card)
                    for nm in nm_list:
                        if nm.buttons and any(b for row in nm.buttons for b in row if any(q in b.text for q in ["1080", "720", "480"])):
                            card_msg = nm
                            break
                break

            if any(b for row in m.buttons for b in row if any(q in b.text for q in ["1080", "720", "480"])):
                card_msg = m
                break

        if not card_msg:
            async for nm in self.client.iter_messages(bot, limit=3):
                if nm.buttons and any(b for row in nm.buttons for b in row if any(q in b.text for q in ["1080", "720", "480"])):
                    card_msg = nm
                    break

        if not card_msg or not card_msg.buttons:
            logger.warning(f"[@{bot}] Film kartasi yoki sifat tugmalari topilmadi.")
            return None

        # 3. Sifat tugmasini tanlash va bosish
        quality_btns = {}
        for r_idx, row in enumerate(card_msg.buttons):
            for c_idx, btn in enumerate(row):
                t = btn.text
                if "720" in t:
                    quality_btns["720p"] = (r_idx, c_idx, t)
                elif "1080" in t:
                    quality_btns["1080p"] = (r_idx, c_idx, t)
                elif "480" in t:
                    quality_btns["480p"] = (r_idx, c_idx, t)

        logger.info(f"Mavjud sifatlar: {list(quality_btns.keys())}")
        chosen = quality_btns.get("720p") or quality_btns.get("1080p") or quality_btns.get("480p")
        if not chosen:
            for r_idx, row in enumerate(card_msg.buttons):
                for c_idx, btn in enumerate(row):
                    if btn.data:
                        chosen = (r_idx, c_idx, btn.text)
                        break
                if chosen:
                    break

        if not chosen:
            logger.warning("Boshqa sifat tugmasi topilmadi!")
            return None

        r_idx, c_idx, q_name = chosen
        logger.info(f"Sifat tugmasi bosilmoqda: '{q_name}'...")
        quality_click_id = card_msg.id
        await card_msg.click(r_idx, c_idx)

        # 4. Video kelishini tezkor kutamiz
        logger.info("Video xabari kelishi kutilmoqda...")
        def is_valid_vid(m):
            if not m.file:
                return False
            if m.file.name and m.file.name.lower().endswith(('.mp4', '.mkv', '.avi', '.mov')):
                return True
            if getattr(m, 'video', None) is not None:
                return True
            mime = getattr(getattr(m, 'document', None), 'mime_type', '')
            return bool(mime and mime.startswith('video/'))

        def has_asil_video(msgs):
            return any(is_valid_vid(vm) for vm in msgs)

        video_replies = await poll_new_messages(self.client, bot, quality_click_id, timeout=20.0, interval=0.4, condition=has_asil_video)
        for vm in video_replies:
            if is_valid_vid(vm):
                v_name = vm.file.name or f"video_{vm.id}.mp4"
                size_mb = round(vm.file.size / (1024 * 1024), 1)
                logger.info(f"🎬 Video keldi: {v_name} ({size_mb} MB) [Msg ID: {vm.id}]")
                if size_mb > max_file_size_mb and "480p" in quality_btns and chosen[2] != quality_btns["480p"][2]:
                    logger.warning(f"⚠️ Video hajmi ({size_mb}MB) 2GB dan katta! 480p tanlanmoqda...")
                    f_r, f_c, f_name = quality_btns["480p"]
                    f_click_id = vm.id
                    await card_msg.click(f_r, f_c)
                    f_replies = await poll_new_messages(self.client, bot, f_click_id, timeout=15.0, interval=0.4, condition=has_asil_video)
                    for f_vm in f_replies:
                        if f_vm.file and f_vm.id != vm.id:
                            return f_vm
                return vm

        return None

    async def _upload_video_to_chat(
        self,
        video_msg: Message,
        target_chat: int,
        reply_to: Optional[int],
        caption: str
    ) -> Optional[Message]:
        """
        Telegram serverlaridan vaqtinchalik yuklab olib, belgilangan chat/topicga yuboradi.
        Diskdagi vaqtinchalik fayl finally: blokida darhol o'chiriladi (0 bayt qoldiq).
        """
        file_path = None
        try:
            peer = await self.client.get_input_entity(target_chat)
            # Server-side copy (juda tez, agar ruxsat berilgan bo'lsa):
            try:
                sent_msg = await self.client.send_file(
                    peer,
                    file=video_msg.media,
                    caption=caption,
                    reply_to=reply_to,
                    supports_streaming=True,
                    parse_mode="html"
                )
                if sent_msg:
                    logger.info("⚡ Server-side nusxalash muvaffaqiyatli bajarildi!")
                    return sent_msg
            except Exception as copy_err:
                logger.info(f"Server-side nusxalab bo'lmadi ({copy_err}), yuklab yuklash usuli bajarilmoqda...")

            # Yuklab yuklash (himoyalangan botlar uchun yagona to'g'ri MTProto yo'li)
            downloads_dir = os.path.join(BASE_DIR, "scraper", "downloads")
            os.makedirs(downloads_dir, exist_ok=True)

            last_logged = [0.0]
            def dl_progress(current, total):
                now = time.time()
                if now - last_logged[0] >= 3.0 or current == total:
                    pct = round(current / total * 100, 1) if total else 0
                    mb_cur = round(current / 1024 / 1024, 1)
                    mb_tot = round(total / 1024 / 1024, 1)
                    logger.info(f"  📥 Yuklab olish: {pct}% ({mb_cur}MB / {mb_tot}MB)")
                    last_logged[0] = now

            logger.info("⚡ Parallel 8-oqimli tezkor yuklab olish boshlandi...")
            raw_filename = video_msg.file.name if (video_msg.file and video_msg.file.name) else f"video_{video_msg.id}.mp4"
            target_file_path = os.path.join(downloads_dir, raw_filename)

            try:
                file_path = await fast_download(
                    client=self.client,
                    location_or_msg=video_msg,
                    out_file_path=target_file_path,
                    progress_callback=dl_progress,
                    connection_count=8
                )
            except Exception as dl_err:
                logger.warning(f"Fast download da xatolik ({dl_err}), standart usulga o'tilmoqda...")
                file_path = await self.client.download_media(video_msg, file=downloads_dir, progress_callback=dl_progress)

            if not file_path or not os.path.exists(file_path):
                logger.error("Videoni yuklab olib bo'lmadi!")
                return None

            total_mb = round(os.path.getsize(file_path) / 1024 / 1024, 1)
            logger.info(f"⚡ Parallel 8-oqimli chatga yuklash boshlandi ({total_mb} MB)...")

            last_ul = [0.0]
            def ul_progress(current, total):
                now = time.time()
                if now - last_ul[0] >= 3.0 or current == total:
                    pct = round(current / total * 100, 1) if total else 0
                    mb_cur = round(current / 1024 / 1024, 1)
                    mb_tot = round(total / 1024 / 1024, 1)
                    logger.info(f"  📤 Yuklash: {pct}% ({mb_cur}MB / {mb_tot}MB)")
                    last_ul[0] = now

            peer = await self.client.get_input_entity(target_chat)
            sent_msg = None
            try:
                uploaded_input_file = await fast_upload(
                    client=self.client,
                    file_path=file_path,
                    progress_callback=ul_progress,
                    connection_count=8
                )
                # Original video atributlaridan foydalanish (aniq duration, width, height va streaming saqlanadi):
                if hasattr(video_msg, "document") and video_msg.document and video_msg.document.attributes:
                    attrs = video_msg.document.attributes
                    mime = getattr(video_msg.document, "mime_type", None) or "video/mp4"
                else:
                    attrs, mime = utils.get_attributes(file_path, supports_streaming=True)

                sent_msg = await self.client.send_file(
                    peer,
                    file=uploaded_input_file,
                    attributes=attrs,
                    mime_type=mime,
                    caption=caption,
                    reply_to=reply_to,
                    supports_streaming=True,
                    parse_mode="html"
                )
            except Exception as ul_err:
                logger.warning(f"Fast upload da xatolik ({ul_err}), standart send_file ga o'tilmoqda...")
                sent_msg = await self.client.send_file(
                    peer,
                    file=file_path,
                    caption=caption,
                    reply_to=reply_to,
                    supports_streaming=True,
                    parse_mode="html",
                    progress_callback=ul_progress
                )
            return sent_msg

        except Exception as e:
            logger.error(f"Videoni ko'chirishda xatolik: {e}")
            return None
        finally:
            # QAT'IY TALAB: Diskda hech qanday fayl qolmasligi va tozalanishi
            if file_path and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                    logger.info(f"🧹 Vaqtinchalik fayl diskdan to'liq o'chirildi: {os.path.basename(file_path)}")
                except Exception as del_err:
                    logger.warning(f"Vaqtinchalik faylni o'chirishda xatolik: {del_err}")


async def main_cli():
    import argparse
    parser = argparse.ArgumentParser(description="Telethon Moderator Pipeline")
    parser.add_argument("--code", type=str, default=None, help="Film ID yoki kodi (masalan: 18506)")
    parser.add_argument("--movie", type=str, default=None, help="Film nomi (masalan: Shiddatli Hujum)")
    parser.add_argument("--series", type=str, default=None, help="Serial nomi (masalan: Erta bahor)")
    parser.add_argument("--year", type=int, default=None, help="Film/Serial yili (masalan: 2026)")
    parser.add_argument("--target", type=str, default="asilmedia", help="Target bot (asilmedia yoki uzmovi)")
    args = parser.parse_args()

    bot_username = TARGET_BOTS.get(args.target, args.target)
    checker = DuplicateChecker()
    await checker.refresh_cache(force=True)

    client = create_telethon_client()
    await client.connect()
    pipeline = TelethonModeratorPipeline(client=client, duplicate_checker=checker)
    try:
        if args.code:
            await pipeline.run_by_code(code=args.code, target_bot=bot_username)
        elif args.series:
            item = QueueItem(
                id=f"{args.target}_{int(time.time())}",
                source=args.target,
                title=args.series,
                year=args.year,
                media_type="series"
            )
            await pipeline.run_single_series(item=item, target_bot=bot_username)
        elif args.movie:
            item = QueueItem(
                id=f"{args.target}_{int(time.time())}",
                source=args.target,
                title=args.movie,
                year=args.year,
                media_type="movie"
            )
            await pipeline.run_single_movie(item=item, target_bot=bot_username)
        else:
            print("Iltimos, --movie, --series yoki --code parametrini kiriting.")
    finally:
        await client.disconnect()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    asyncio.run(main_cli())

