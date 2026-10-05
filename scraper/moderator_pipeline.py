"""
Moderator Pipeline for Kinochi Project.
Implements the exact moderator movie upload cycle:
1. Verify video from target bot (@UzmovieTV_Bot / @asilmediabot).
2. Enrich metadata via TMDb (with full fallback to source site / bot caption if not on TMDb).
3. Create Movie in PostgreSQL database (generates unique code, e.g. 5DSM32).
4. Create Forum Topic in Telegram 'manba' supergroup (AUTO_TOPIC_CHAT_ID) with intro banner.
5. Forward/copy video directly into that specific Forum Topic.
6. Copy video to Private Storage Channel (STORAGE_CHANNEL_ID) and link video to website (playable online).
7. Send confirmation into topic and complete queue item.
"""

import os
import re
import html
import asyncio
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

import logging
import time
from typing import Optional, Dict, Any, Tuple

from dotenv import load_dotenv

# Ensure root directory and backend are in sys.path
import sys
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(BASE_DIR, "backend", ".env"))
load_dotenv(os.path.join(BASE_DIR, "bot", ".env"))
if os.path.join(BASE_DIR, "backend") not in sys.path:
    sys.path.insert(0, os.path.join(BASE_DIR, "backend"))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from pyrogram.types import Message
from pyrogram.errors import ChatForwardsRestricted

from scraper.config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    BOT_TOKEN,
    STORAGE_CHANNEL_ID,
    AUTO_TOPIC_CHAT_ID,
    TARGET_BOTS
)
from scraper.queue_manager import QueueItem
from scraper.duplicate_checker import DuplicateChecker, extract_title_variants

# Backend components
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.repositories.movie_repo import MovieRepositoryImpl
from app.application.movies.service import MovieService
from app.infrastructure.external.tmdb_client import tmdb_client
from app.infrastructure.external.translator import translator_service
from app.infrastructure.external.genre_mapper import map_tmdb_genres
from app.infrastructure.telegram.telegram_client import telegram_client
from scraper.smart_enricher import enrich_movie_smart, clean_movie_title

logger = logging.getLogger(__name__)


async def enrich_movie_metadata(
    raw_title: str,
    year: Optional[int] = None,
    source_poster: Optional[str] = None,
    source_desc: Optional[str] = None,
    source_genres: Optional[str] = None
) -> Dict[str, Any]:
    """
    Kinoning ma'lumotlarini to'ldiradi:
    1. Avval TMDb dan qidiradi (agar xalqaro kino bo'lsa).
    2. Agar TMDb da TOPILMASA (mahalliy o'zbek kinolari yoki doramalar bo'lsa):
       manba sayt yoki bot captionidagi ma'lumotlar bilan to'ldiradi (FALLBACK).
    """
    clean_title = raw_title.split('/')[0].split('|')[0].strip()
    clean_title = re.sub(r'\(.*?\)', '', clean_title).strip()
    clean_title = re.sub(r'^\d+\s+', '', clean_title).strip()

    metadata = {
        "title": clean_title or raw_title,
        "original_title": None,
        "description": source_desc or f"🍿 {clean_title} ({year or 'premyera'}) kinofilmi o'zbek tilida.",
        "poster_url": source_poster,
        "release_year": year,
        "imdb_rating": None,
        "tmdb_rating": None,
        "tmdb_id": None,
        "genres": source_genres or "Tarjima kino",
        "cast": None,
        "director": None,
        "source_used": "fallback_site"
    }

    # ── 1-BOSQICH: TMDb dan qidirish ──
    try:
        search_results = await tmdb_client.search(query=clean_title, content_type="movie")
        matched_tmdb = None

        if search_results:
            # Agar yil bo'lsa, yilga eng yaqinini tanlaymiz
            if year:
                for res in search_results:
                    res_year = res.get("year")
                    if res_year and abs(res_year - year) <= 1:
                        matched_tmdb = res
                        break
            if not matched_tmdb:
                matched_tmdb = search_results[0]

        if matched_tmdb and matched_tmdb.get("id"):
            tmdb_id = matched_tmdb["id"]
            details = await tmdb_client.get_details(tmdb_id=tmdb_id, content_type="movie")
            if details:
                # O'zbekcha tarjima
                raw_overview = details.get("overview") or ""
                translated_desc, _ = await translator_service.translate_to_uzbek(raw_overview)
                
                raw_title_tmdb = details.get("title") or clean_title
                orig_title_tmdb = details.get("original_title") or ""
                uz_title, _ = await translator_service.translate_title_to_uzbek(raw_title_tmdb, orig_title_tmdb)

                uz_genres = map_tmdb_genres(details.get("genres_raw", []))
                genres_str = ", ".join(uz_genres) if uz_genres else details.get("genres_str", "")

                metadata["title"] = uz_title or raw_title_tmdb
                metadata["original_title"] = orig_title_tmdb
                metadata["description"] = translated_desc or metadata["description"]
                metadata["poster_url"] = details.get("poster_url") or source_poster
                metadata["release_year"] = details.get("release_year") or year
                metadata["imdb_rating"] = details.get("imdb_rating")
                metadata["tmdb_rating"] = details.get("tmdb_rating")
                metadata["tmdb_id"] = tmdb_id
                metadata["genres"] = genres_str or metadata["genres"]
                metadata["cast"] = details.get("cast")
                metadata["director"] = details.get("director")
                metadata["source_used"] = "tmdb"
                logger.info(f"✅ TMDb dan muvaffaqiyatli ma'lumot olindi: '{metadata['title']}' (ID: {tmdb_id})")
    except Exception as e:
        logger.warning(f"TMDb qidirishda xatolik yuz berdi (fallback ishlatiladi): {e}")

    return metadata


class ModeratorPipeline:
    """
    Websaytdagi moderator kino yuklash siklini to'liq avtomatlashtirilgan shaklda bajaruvchi sinf.
    """
    def __init__(self, userbot_client, duplicate_checker: DuplicateChecker):
        self.app = userbot_client
        self.dup_checker = duplicate_checker

    async def run_single_movie(
        self,
        item: QueueItem,
        target_bot: str = "UzmovieTV_Bot"
    ) -> bool:
        """
        Bitta kino uchun to'liq moderator siklini bajaradi:
        1. Dublikatni tekshirish
        2. Target botdan videoni olish
        3. TMDb / Saytdan ma'lumotlarni to'ldirish
        4. Websayt bazasida kino yaratish (Code generatsiya qilinadi)
        5. 'manba' guruhida alohida Topic ochish va kirish xabarini yuborish
        6. Videoni aynan shu Topic ichiga nusxalash
        7. Private Storage kanalga ko'chirish va websaytda videoni faollashtirish
        """
        logger.info(f"\n=======================================================")
        logger.info(f"🎬 MODERATOR SIKLI BOSHLANDI: '{item.title}' ({item.year or 'Noma\'lum'})")
        logger.info(f"=======================================================")

        # ── 1. DUBLIKAT TEKSHIRUVI ──
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
            return False

        video_msg = await self._fetch_video_from_bot(item=item, target_bot=target_bot)
        if not video_msg:
            logger.warning(f"❌ '{item.title}' bo'yicha @{target_bot} dan video olinmadi.")
            return False

        return await self._process_movie_pipeline(item=item, video_msg=video_msg, target_bot=target_bot)

    async def run_by_code(
        self,
        code: str,
        target_bot: str = "UzmovieTV_Bot"
    ) -> bool:
        """
        Target botdan (masalan @UzmovieTV_Bot) film kodi bo'yicha to'liq moderator siklini bajaradi:
        1. Kod yuboriladi va video olinadi
        2. Captiondan sarlavha va yil ajratiladi
        3. Dublikat tekshiriladi
        4. TMDb ma'lumotlari (yoki fallback) to'ldiriladi
        5. PostgreSQL bazada kino yaratiladi (#kod beriladi)
        6. 'manba' guruhida alohida Topic ochiladi
        7. Video shu Topicga joylanadi
        8. Private Storage kanalga ko'chiriladi va Websaytda video faollashtiriladi
        """
        logger.info(f"\n=======================================================")
        logger.info(f"🎬 MODERATOR SIKLI: KOD #{code} | TARGET BOT: @{target_bot}")
        logger.info(f"=======================================================")

        video_msg = await self._fetch_video_from_bot(code=code, target_bot=target_bot)
        if not video_msg:
            logger.warning(f"❌ Kod #{code} bo'yicha botdan video olinmadi yoki film topilmadi.")
            return False

        caption = video_msg.caption or video_msg.text or ""
        caption_title_m = re.search(r'🎬\s*([^\n\r–]+)', caption)
        if caption_title_m:
            raw_title = clean_movie_title(caption_title_m.group(1))
        else:
            raw_title = f"Film #{code}"

        caption_year = None
        year_m = re.search(r'Yil:\s*(\d{4})', caption, re.I)
        if year_m:
            caption_year = int(year_m.group(1))
        else:
            file_name = ""
            if video_msg.video and video_msg.video.file_name:
                file_name = video_msg.video.file_name
            elif video_msg.document and video_msg.document.file_name:
                file_name = video_msg.document.file_name
            y_m2 = re.search(r'\b(19\d{2}|20\d{2})\b', caption + " " + file_name)
            if y_m2:
                caption_year = int(y_m2.group(1))

        item = QueueItem(
            id=f"{target_bot.lower()}_{code}",
            source="asilmedia" if "asil" in target_bot.lower() else "uzmovi",
            title=raw_title,
            year=caption_year,
            media_type="movie"
        )

        return await self._process_movie_pipeline(item=item, video_msg=video_msg, target_bot=target_bot)

    async def _process_movie_pipeline(
        self,
        item: QueueItem,
        video_msg: Message,
        target_bot: str
    ) -> bool:
        """
        Baza, Topic, Video va Websaytni birlashtiruvchi yagona moderator sikli.
        """
        # Kelgan video captionidan ma'lumotlarni to'ldiramiz
        caption = video_msg.caption or video_msg.text or ""
        caption_title_m = re.search(r'🎬\s*([^\n\r–]+)', caption)
        caption_title = clean_movie_title(caption_title_m.group(1)) if caption_title_m else clean_movie_title(item.title)
        
        caption_year = item.year
        year_m = re.search(r'Yil:\s*(\d{4})', caption, re.I)
        if year_m:
            caption_year = int(year_m.group(1))
        elif not caption_year:
            file_name = ""
            if video_msg.video and video_msg.video.file_name:
                file_name = video_msg.video.file_name
            elif video_msg.document and video_msg.document.file_name:
                file_name = video_msg.document.file_name
            y_m2 = re.search(r'\b(19\d{2}|20\d{2})\b', caption + " " + file_name)
            if y_m2:
                caption_year = int(y_m2.group(1))

        # ── 1. DUBLIKAT TEKSHIRUVI ──
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
            return False

        # ── 2. METADATA TO'LDIRISH (TMDb YOKI SAYT/BOT FALLBACK) ──
        logger.info("ℹ️ 1-QADAM: Kino ma'lumotlari AI (Gemini) + TMDb orqali shakllantirilmoqda...")
        meta = await enrich_movie_smart(
            raw_title=caption_title or item.title,
            year=caption_year,
            source_poster=item.poster_url,
            source_desc=caption or None,
            caption=caption
        )

        title = meta["title"]
        year = meta["release_year"]
        year_str = f" ({year})" if year else ""

        # ── 3. WEBSAYT BAZASIDA KINO YARATISH (PostgreSQL) ──
        logger.info(f"ℹ️ 2-QADAM: Websayt bazasiga (PostgreSQL) yangi kino qo'shilmoqda: '{title}'...")
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

        # ── 4. 'manba' GURUHIDA TOPIC OCHISH ──
        target_chat = AUTO_TOPIC_CHAT_ID
        if not target_chat:
            logger.error("AUTO_TOPIC_CHAT_ID sozlanmagan!")
            return False

        topic_name = f"🎬 {title}{year_str}"
        logger.info(f"ℹ️ 3-QADAM: Guruhda Forum Topic ochilmoqda: '{topic_name}'...")
        try:
            thread_id = await self._create_topic(chat_id=target_chat, title=topic_name)
            if not thread_id:
                logger.error("Topic ochib bo'lmadi!")
                return False
            logger.info(f"✅ Topic muvaffaqiyatli ochildi! Thread ID: {thread_id}")
        except Exception as e:
            logger.error(f"Topic ochishda xatolik: {e}")
            return False

        # Topic ichiga kirish postini yuborish (Rasm yoki Matn)
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
                    await self.app.send_photo(
                        chat_id=target_chat,
                        photo=meta["poster_url"],
                        caption=welcome_text,
                        reply_to_message_id=thread_id
                    )
                except Exception:
                    await self.app.send_message(
                        chat_id=target_chat,
                        text=welcome_text,
                        reply_to_message_id=thread_id,
                        disable_web_page_preview=False
                    )
            else:
                await self.app.send_message(
                    chat_id=target_chat,
                    text=welcome_text,
                    reply_to_message_id=thread_id
                )
        except Exception as e:
            logger.warning(f"Kirish xabarini yuborishda xatolik: {e}")

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

        # ── 5. VIDEONI AYNAN SHU TOPICGA YUKLASH (Userbot orqali) ──
        logger.info(f"ℹ️ 4-QADAM: Video ochilgan Topic (ID: {thread_id}) ga ko'chirilmoqda...")
        clean_caption = f"🍿 <b>{title}</b>{year_str}\n🔑 <b>Kod:</b> <code>{movie_code}</code>"

        topic_video_msg = await self._copy_or_upload_video(
            video_msg=video_msg,
            target_chat=target_chat,
            topic_id=thread_id,
            caption=clean_caption
        )
        if not topic_video_msg:
            logger.error("Videoni Topic ichiga ko'chirib bo'lmadi!")
            return False

        logger.info(f"✅ Video Topic ichiga muvaffaqiyatli joylashtirildi! (Message ID: {topic_video_msg.id})")

        # ── 6. PRIVATE STORAGE KANALGA KO'CHIRISH VA WEBSAYTDA LINK QILISH ──
        logger.info(f"ℹ️ 5-QADAM: Video asosiy Private Storage kanalga saqlanmoqda va Websaytga ulanmoqda...")
        storage_chat = STORAGE_CHANNEL_ID
        storage_caption = (
            f"🍿 <b>{html.escape(title)}</b>\n"
            f"🔑 <b>Kodi:</b> <code>{movie_code}</code>\n"
            + (f"📅 <b>Yili:</b> {year}\n" if year else "")
        )

        # Topicdagi videodan Storage kanalga nusxalash (server-side copy, himoyasiz, juda tez!)
        storage_msg = await self._copy_or_upload_video(
            video_msg=topic_video_msg,
            target_chat=storage_chat,
            topic_id=None,
            caption=storage_caption
        )
        if not storage_msg:
            logger.warning("Storage kanalga nusxalashda xatolik yuz berdi, lekin video Topicda mavjud.")
            return True

        # Video fayl ID si va storage message ID sini websayt bazasiga ulaymiz
        telegram_file_id = None
        if storage_msg.video:
            telegram_file_id = storage_msg.video.file_id
        elif storage_msg.document:
            telegram_file_id = storage_msg.document.file_id

        async with async_session_factory() as session:
            repo = MovieRepositoryImpl(session)
            service = MovieService(repo)
            await service.link_movie_video_from_message(
                movie_id=movie_id,
                message_id=storage_msg.id,
                language="Asosiy",
                telegram_file_id=telegram_file_id
            )
            await session.commit()
            logger.info(f"🎉 WEBSAYTDA VIDEO TO'LIQ FAOLLASHTIRILDI! Onlayn tomosha qilishga tayyor! (Kod: #{movie_code})")

        # Websayt keshi tozalanadi
        try:
            from app.core.cache import delete_cache_pattern
            await delete_cache_pattern("cache:movies:*")
        except Exception:
            pass

        # Topic ichiga tasdiqlash xabari yuboramiz
        confirm_text = (
            f"✅ <b>Kino videosi saqlandi va indekslandi.</b>\n"
            f"🔑 Kod: <code>{movie_code}</code>\n"
            f"🌐 Websaytda onlayn tomosha qilishga tayyor!"
        )
        try:
            await self.app.send_message(
                chat_id=target_chat,
                text=confirm_text,
                reply_to_message_id=thread_id
            )
        except Exception as e:
            logger.warning(f"Tasdiqlash xabarini yuborishda xatolik: {e}")

        return True

    async def _create_topic(self, chat_id: int, title: str) -> Optional[int]:
        """Userbot orqali superguruhda Forum Topic ochadi va thread_id qaytaradi."""
        try:
            import random
            from pyrogram import raw
            peer = await self.app.resolve_peer(chat_id)
            r_id = random.randint(1, 2**31 - 1)
            res = await self.app.invoke(raw.functions.channels.CreateForumTopic(
                channel=peer,
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
            logger.error(f"Userbot orqali topic ochishda xatolik: {e}")
            return None

    async def _fetch_video_from_bot(
        self,
        item: Optional[QueueItem] = None,
        target_bot: str = "UzmovieTV_Bot",
        code: Optional[str] = None
    ) -> Optional[Message]:
        """
        Target botdan video xabarini oladi:
        1. UzmovieTV_Bot: Kod yuboriladi (masalan 15, 20).
        2. asilmediabot: Nomi yoki /start ID yuboriladi, tugmalar bosiladi.
        """
        is_uzmovie = "uzmovie" in target_bot.lower()
        search_query = ""

        if code:
            search_query = str(code).strip()
        elif item:
            num_match = re.search(r'\b\d+\b', item.id)
            if is_uzmovie and num_match and len(num_match.group(0)) <= 4:
                search_query = num_match.group(0)
            else:
                clean_name = item.title.split('/')[0].split('|')[0].strip()
                clean_name = re.sub(r'\(.*?\)', '', clean_name).strip()
                clean_name = re.sub(r'^\d+\s+', '', clean_name).strip()
                search_query = clean_name

        if not search_query:
            logger.warning("Botga yuborish uchun so'rov yoki kod topilmadi!")
            return None

        if not is_uzmovie:
            # Asilmedia bot flow: MTProto Layer 229 orqali zamonaviy foto/inline tugmalarni boshqarish
            from scraper.asilmedia_client import AsilmediaBotClient
            session_path = os.path.join(os.path.dirname(__file__), "kinochi_userbot")
            asil_client = AsilmediaBotClient(session_path, TELEGRAM_API_ID, TELEGRAM_API_HASH)
            try:
                await asil_client.connect()
                year = item.year if item else None
                msg_id = await asil_client.fetch_video_message_id(query=search_query, year=year)
                if msg_id:
                    pyro_msg = await self.app.get_messages(target_bot, msg_id)
                    return pyro_msg
            except Exception as e:
                logger.error(f"Asilmedia botdan video olishda xatolik: {e}")
            finally:
                await asil_client.disconnect()
            return None

        # UzmovieTV_Bot flow
        logger.info(f"[{target_bot}] botiga so'rov yuborilmoqda: '{search_query}'...")
        sent = await self.app.send_message(target_bot, search_query)
        await asyncio.sleep(3.5)

        replies = []
        async for m in self.app.get_chat_history(target_bot, limit=8):
            if m.id > sent.id:
                replies.append(m)

        for m in replies:
            if m.video or (m.document and m.document.mime_type and m.document.mime_type.startswith("video/")):
                return m

        for m in replies:
            if m.text and any(x in m.text.lower() for x in ["topilmadi", "mavjud emas"]):
                logger.warning(f"[{target_bot}] Film topilmadi deb javob berdi: {m.text}")
                return None

        return None

    async def _copy_or_upload_video(
        self,
        video_msg: Message,
        target_chat: int,
        topic_id: Optional[int],
        caption: str
    ) -> Optional[Message]:
        """Videoni guruhga yoki kanalga nusxalaydi (agar protected bo'lsa yuklab yuboradi)."""
        try:
            copied = await self.app.copy_message(
                chat_id=target_chat,
                from_chat_id=video_msg.chat.id,
                message_id=video_msg.id,
                caption=caption,
                reply_to_message_id=topic_id
            )
            return copied
        except Exception as copy_err:
            err_str = str(copy_err)
            if "CHAT_FORWARDS_RESTRICTED" in err_str or isinstance(copy_err, ChatForwardsRestricted):
                logger.info("⚠️ [Himoyalangan video]: Target bot kontentni himoyalagan (CHAT_FORWARDS_RESTRICTED).")
                logger.info("⬇️ Telegram serverlaridan vaqtinchalik yuklab olinmoqda...")
                
                last_logged = [0.0]
                def dl_progress(current, total):
                    now = time.time()
                    if now - last_logged[0] >= 3.0 or current == total:
                        pct = round(current / total * 100, 1) if total else 0
                        mb_cur = round(current / 1024 / 1024, 1)
                        mb_tot = round(total / 1024 / 1024, 1)
                        logger.info(f"  📥 Yuklab olish: {pct}% ({mb_cur}MB / {mb_tot}MB)")
                        last_logged[0] = now

                file_path = await self.app.download_media(video_msg, progress=dl_progress)
                if not file_path or not os.path.exists(file_path):
                    logger.error("Videoni yuklab olib bo'lmadi!")
                    return None
                
                total_mb = round(os.path.getsize(file_path) / 1024 / 1024, 1)
                logger.info(f"⬆️ Topicga yuklanmoqda ({total_mb} MB)...")
                last_ul = [0.0]
                def ul_progress(current, total):
                    now = time.time()
                    if now - last_ul[0] >= 3.0 or current == total:
                        pct = round(current / total * 100, 1) if total else 0
                        mb_cur = round(current / 1024 / 1024, 1)
                        mb_tot = round(total / 1024 / 1024, 1)
                        logger.info(f"  📤 Topicga yuklash: {pct}% ({mb_cur}MB / {mb_tot}MB)")
                        last_ul[0] = now

                duration = video_msg.video.duration if video_msg.video else 0
                width = video_msg.video.width if video_msg.video else 0
                height = video_msg.video.height if video_msg.video else 0

                try:
                    sent = await self.app.send_video(
                        chat_id=target_chat,
                        video=file_path,
                        caption=caption,
                        duration=duration,
                        width=width,
                        height=height,
                        reply_to_message_id=topic_id,
                        supports_streaming=True,
                        progress=ul_progress
                    )
                    return sent
                except Exception as send_err:
                    logger.warning(f"send_video muvaffaqiyatsiz bo'ldi ({send_err}), send_document sinab ko'rilmoqda...")
                    try:
                        sent = await self.app.send_document(
                            chat_id=target_chat,
                            document=file_path,
                            caption=caption,
                            reply_to_message_id=topic_id,
                            progress=ul_progress
                        )
                        return sent
                    except Exception as doc_err:
                        logger.error(f"Faylni yuborib bo'lmadi: {doc_err}")
                        return None
                finally:
                    if file_path and os.path.exists(file_path):
                        try:
                            os.remove(file_path)
                        except Exception:
                            pass
            else:
                logger.error(f"Videoni ko'chirishda kutilmagan xatolik: {copy_err}")
                return None
