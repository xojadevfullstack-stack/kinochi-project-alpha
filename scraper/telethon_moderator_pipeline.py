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
from telethon.sessions import MemorySession, StringSession
from telethon.crypto import AuthKey
from telethon.tl.functions.messages import CreateForumTopicRequest
from telethon.tl.types import Message
from telethon.errors import FloodWaitError
from scraper.fast_telethon import fast_download, fast_upload

from scraper.config import (
    TELEGRAM_API_ID,
    TELEGRAM_API_HASH,
    TELEGRAM_STRING_SESSION,
    BOT_TOKEN,
    STORAGE_CHANNEL_ID,
    AUTO_TOPIC_CHAT_ID,
    TARGET_BOTS
)
from scraper.queue_manager import QueueManager, QueueItem
from scraper.duplicate_checker import DuplicateChecker
from scraper.smart_enricher import enrich_movie_smart, clean_movie_title
from scraper.state_manager import StateManager

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

FALLBACK_USERBOT_SESSION = (
    "1ApWapzMBuyF503SKFe7YvecikokTfoWvtlnlzunbRRik8mht2VtaJve7uOtwuKwQBdXkvZ_0cOn-SBVZ2jHcHJuRhdcGiVBnP_Yg0_dEVOJT6jjvVhbwepZFPTn4HkwyVqG2Z7h-HFpXRYo4HboCGLR0QCYVx8KrKVQYTK44Sxiai6atXQ7klb6tKg_Nq8S2u3x23V82J3SVM6bROoGvltvZKMZ2n9suDPUSWtg9612fCtTqsH6ohVEq-jeWUt099pWYWCBnn_yTlWiZWdhflktlGP4nD4PL52JdQDz1zUilq1B9KFsLq8DQW3jbfYzbpAzz6175F_Ve3xuD2-wsBd8--H08Is0="
)


def create_telethon_client(session_path: str = None) -> TelegramClient:
    """
    Telethon mijozini yaratadi:
    1. Environment variable (TELEGRAM_STRING_SESSION) orqali (Docker va Cloud serverlar uchun).
    2. Mavjud va to'g'ri .session fayl orqali.
    3. Zaxira sessiya orqali (fayl bo'lmaganda yoki buzilganda ham uzluksiz ishlash uchun).
    """
    raw_str_session = (
        os.environ.get("TELEGRAM_STRING_SESSION")
        or TELEGRAM_STRING_SESSION
        or os.environ.get("USERBOT_SESSION_STRING")
        or os.environ.get("TELETHON_SESSION")
    )
    if raw_str_session and str(raw_str_session).strip():
        logger.info("Telethon mijozini TELEGRAM_STRING_SESSION orqali yuklash...")
        return TelegramClient(StringSession(str(raw_str_session).strip()), TELEGRAM_API_ID, TELEGRAM_API_HASH)

    session_file = session_path or os.path.join(BASE_DIR, "scraper", "kinochi_userbot.session")
    if not session_file.endswith(".session"):
        session_file += ".session"

    if os.path.exists(session_file) and os.path.getsize(session_file) > 100:
        try:
            conn = sqlite3.connect(session_file)
            c = conn.cursor()
            c.execute("SELECT dc_id, auth_key FROM sessions")
            row = c.fetchone()
            conn.close()

            if row:
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
        except Exception as e:
            logger.warning(f"Session faylidan o'qishda xatolik: {e}")

    logger.info("Zaxira Telegram StringSession orqali ulanmoqda...")
    return TelegramClient(StringSession(FALLBACK_USERBOT_SESSION), TELEGRAM_API_ID, TELEGRAM_API_HASH)


def is_bot_flood_text(text: Optional[str]) -> bool:
    if not text:
        return False
    t = text.lower()
    return any(p in t for p in [
        "biroz sekinroq",
        "bir daqiqadan so'ng",
        "daqiqadan so'ng urinib",
        "sekinroq",
        "juda ko'p so'rov",
        "flood",
        "kutib turing",
        "biroz kuting"
    ])


def get_flood_wait_seconds(msg_or_msgs: Any) -> int:
    if not msg_or_msgs:
        return 0
    msgs = msg_or_msgs if isinstance(msg_or_msgs, list) else [msg_or_msgs]
    for m in msgs:
        text = getattr(m, "text", None) or getattr(m, "message", None) or (m if isinstance(m, str) else "")
        if not text:
            continue
        t = str(text).lower()
        if is_bot_flood_text(t):
            m_sec = re.search(r'(\d+)\s*(?:soniya|sekund)', t)
            if m_sec:
                return int(m_sec.group(1)) + 5
            m_min = re.search(r'(\d+)\s*(?:daqiqa|minut)', t)
            if m_min:
                return int(m_min.group(1)) * 60 + 5
            return 65  # Default "Bir daqiqadan so'ng urinib ko'ring" -> 60s + 5s zaxira
    return 0


def is_video_message(m: Any) -> bool:
    """
    Xabar video yoki video-fayl ekanligini ishonchli aniqlash.
    Telethon video xabarlari, .m4v, .mp4, .mkv, .avi, .webm, .flv, .ts formatlarini qamrab oladi.
    """
    if not m:
        return False
    if getattr(m, "video", None):
        return True
    if getattr(m, "document", None):
        doc = m.document
        if getattr(doc, "mime_type", "").startswith("video/"):
            return True
        for attr in getattr(doc, "attributes", []):
            if type(attr).__name__ == "DocumentAttributeVideo":
                return True
            if type(attr).__name__ == "DocumentAttributeFilename":
                fn = getattr(attr, "file_name", "").lower()
                if any(fn.endswith(ext) for ext in (".mp4", ".mkv", ".avi", ".mov", ".m4v", ".webm", ".flv", ".ts")):
                    return True
    if getattr(m, "file", None) and getattr(m.file, "name", None):
        fn = m.file.name.lower()
        if any(fn.endswith(ext) for ext in (".mp4", ".mkv", ".avi", ".mov", ".m4v", ".webm", ".flv", ".ts")):
            return True
    return False


def matches_episode(m: Any, ep_num: int, total_eps: int = 12) -> bool:
    """
    Video xabar berilgan qism raqamiga (ep_num) mos kelishini aniqlash.
    """
    if total_eps == 1:
        return True
    fn = (getattr(getattr(m, "file", None), "name", "") or "").lower()
    tx = (getattr(m, "text", "") or getattr(m, "caption", "") or "").lower()
    ep_patterns = [
        rf"\b{ep_num}\s*[-_]?\s*qism\b",
        rf"\b{ep_num}\s*[-_]?\s*seriya\b",
        rf"\b{ep_num}\s*[-_]?\s*ep\b",
        rf"\bq0*{ep_num}\b",
        rf"\bep0*{ep_num}\b",
        rf"\bf\d+q0*{ep_num}\b",
    ]
    for pat in ep_patterns:
        if re.search(pat, fn) or re.search(pat, tx):
            return True
    other_ep_found = False
    for other in range(1, total_eps + 5):
        if other == ep_num:
            continue
        if re.search(rf"\b{other}\s*[-_]?\s*qism\b", fn) or re.search(rf"\b{other}\s*[-_]?\s*qism\b", tx):
            other_ep_found = True
            break
        if re.search(rf"\bq0*{other}\b", fn) or re.search(rf"\bf\d+q0*{other}\b", fn):
            other_ep_found = True
            break
    if not other_ep_found:
        return True
    return False


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
    Agar botdan flood xabari kelsa, timeoutni kutmasdan darhol qaytaradi.
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        await asyncio.sleep(interval)
        msgs = []
        try:
            async for m in client.iter_messages(chat, limit=8):
                if m.id > after_id:
                    msgs.append(m)
        except FloodWaitError as e:
            logger.warning(f"Telegram FloodWaitError: {e.seconds} soniya kutilmoqda...")
            try:
                StateManager().set_bot_status("flood_wait")
            except Exception:
                pass
            await asyncio.sleep(e.seconds + 2)
            try:
                StateManager().set_bot_status("online")
            except Exception:
                pass
            continue
        except Exception:
            pass

        if msgs:
            # Agar bot flood / sekinroq xabari yuborgan bo'lsa, timeout tugashini kutmasdan darhol qaytarish
            for m in msgs:
                if is_bot_flood_text(m.text):
                    return msgs
            if condition is None or condition(msgs):
                return msgs
    return []


class TelethonModeratorPipeline:
    def __init__(self, client: TelegramClient, duplicate_checker: DuplicateChecker):
        self.client = client
        self.dup_checker = duplicate_checker
        self._last_card_msg: Optional[Message] = None

    async def safe_click(self, msg: Message, row: int, col: int) -> tuple[bool, int]:
        """
        Tugmani xavfsiz bosadi.
        Qaytaradi: (success: bool, flood_wait_seconds: int)
        """
        try:
            res = await asyncio.wait_for(msg.click(row, col), timeout=5.0)
            if res and hasattr(res, 'message') and res.message:
                wait_s = get_flood_wait_seconds(res.message)
                if wait_s > 0:
                    try:
                        StateManager().set_bot_status("flood_wait")
                    except Exception:
                        pass
                    return False, wait_s
            return True, 0
        except asyncio.TimeoutError:
            # Bot callback'ga darhol javob qaytarmasa ham, bosish Telegramga yetkazilgan
            return True, 0
        except FloodWaitError as e:
            try:
                StateManager().set_bot_status("flood_wait")
            except Exception:
                pass
            return False, e.seconds + 5
        except Exception as e:
            logger.debug(f"Click callback xabari: {e}")
            return True, 0

    async def handle_sponsor_lock(self, bot_username: str, msg: Message) -> Optional[Message]:
        """
        Agar bot homiy kanallarga obuna bo'lish talabini qo'ysa,
        Telethon orqali havola kanallarga avtomatik a'zo bo'ladi va
        tasdiqlash/tekshirish tugmasini bosadi.
        """
        if not msg:
            return None
        text = (msg.text or "").lower()
        is_sponsor = any(w in text for w in ["obuna bo'ling", "homiy", "kanalga a'zo", "obuna bo'lmagansiz", "obuna talab"])
        has_verify_btn = False
        if msg.buttons:
            for row in msg.buttons:
                for b in row:
                    if any(w in b.text.lower() for w in ["tekshirish", "animeni ko'rish", "a'zo bo'ldim", "tasdiqlash", "davom etish"]):
                        has_verify_btn = True
                        break

        if not (is_sponsor or has_verify_btn):
            return msg

        logger.info(f"🛡️ [@{bot_username}] Homiy kanallar talabi aniqlandi. Avtomatik obuna bo'linmoqda...")
        print(f"  🛡️ [@{bot_username}] Homiy kanallarga avtomatik ulanmoqda...", flush=True)

        from telethon.tl.functions.messages import ImportChatInviteRequest
        from telethon.tl.functions.channels import JoinChannelRequest
        from telethon.errors import UserAlreadyParticipantError

        verify_coords = None

        for r_i, row in enumerate(msg.buttons or []):
            for c_i, b in enumerate(row):
                b_url = getattr(b, "url", None) or ""
                b_text = b.text.lower()
                if any(w in b_text for w in ["tekshirish", "animeni ko'rish", "a'zo bo'ldim", "tasdiqlash", "davom etish"]):
                    verify_coords = (r_i, c_i)

                if b_url and ("t.me/" in b_url or "telegram.me/" in b_url):
                    # 1. Private invite: t.me/+hash or t.me/joinchat/hash
                    m_inv = re.search(r'(?:t\.me|telegram\.me)/(?:\+|joinchat/)([A-Za-z0-9_-]+)', b_url)
                    if m_inv:
                        inv_hash = m_inv.group(1)
                        try:
                            await self.client(ImportChatInviteRequest(inv_hash))
                            logger.info(f"✅ [@{bot_username}] Homiy kanalga ulandi (+{inv_hash[:6]}...)")
                        except UserAlreadyParticipantError:
                            pass
                        except Exception as e:
                            logger.debug(f"Invite join xatolik: {e}")
                    else:
                        # 2. Public channel: t.me/channel_username
                        m_pub = re.search(r'(?:t\.me|telegram\.me)/([A-Za-z0-9_]{4,})', b_url)
                        if m_pub:
                            pub_uname = m_pub.group(1)
                            if pub_uname.lower() not in ("kawaii_uz_bot", "asilmediabot", "uzmovietv_bot", "share"):
                                try:
                                    await self.client(JoinChannelRequest(pub_uname))
                                    logger.info(f"✅ [@{bot_username}] Homiy kanalga ulandi (@{pub_uname})")
                                except UserAlreadyParticipantError:
                                    pass
                                except Exception as e:
                                    logger.debug(f"Public channel join xatolik: {e}")

        if verify_coords:
            logger.info(f"[@{bot_username}] Tasdiqlash tugmasi bosilmoqda...")
            await asyncio.sleep(1.5)
            await self.safe_click(msg, verify_coords[0], verify_coords[1])
            await asyncio.sleep(2.5)
            updated = await self.client.get_messages(bot_username, ids=msg.id)
            if updated and updated.buttons and not any(w in (updated.text or "").lower() for w in ["obuna bo'ling", "homiy"]):
                return updated
            async for nm in self.client.iter_messages(bot_username, limit=3):
                if nm.buttons and not any(w in (nm.text or "").lower() for w in ["obuna bo'ling", "homiy"]):
                    return nm

        return msg

    async def run_item(self, item: QueueItem, target_bot: str = "asilmediabot", max_episodes: Optional[int] = None) -> bool:
        """Kino yoki Serial turiga qarab mos pipeline siklini ishga tushiradi (qat'iy Timeout bilan)."""
        # Seriallar ko'p qismli bo'lgani uchun 25 daqiqa, bitta kinolar uchun 12 daqiqa timeout
        item_timeout = 1500 if getattr(item, "media_type", "movie") == "series" else 720
        try:
            return await asyncio.wait_for(self._run_item_inner(item, target_bot, max_episodes=max_episodes), timeout=item_timeout)
        except asyncio.TimeoutError:
            logger.error(f"⏱️ '{item.title}' jarayoni {item_timeout // 60} daqiqadan oshdi (Timeout). Keyingi kinoga o'tilmoqda...")
            print(f"⏱️ '{item.title}' jarayoni {item_timeout // 60} daqiqadan oshdi (Timeout). Keyingi kinoga o'tilmoqda...", flush=True)
            return False

    async def _run_item_inner(self, item: QueueItem, target_bot: str = "asilmediabot", max_episodes: Optional[int] = None) -> bool:
        try:
            StateManager().set_bot_status("online")
        except Exception:
            pass

        # Item manbasiga qarab mos botni avtomatik aniqlash:
        # Asilmedia kodlari (@asilmediabot), Uzmovi kodlari (@UzmovieTV_Bot), Kawaii (@kawaii_uz_bot) da ishlaydi
        if getattr(item, "source", None) == "kawaii" or target_bot in ("kawaii", "kawaii_uz_bot"):
            return await self.run_kawaii_anime(item=item, max_episodes=max_episodes)

        effective_bot = target_bot
        if getattr(item, "source", None) == "asilmedia":
            effective_bot = "asilmediabot"
        elif getattr(item, "source", None) == "uzmovi":
            effective_bot = "UzmovieTV_Bot"

        if item.media_type == "series":
            # UzmovieTV_Bot da seriallar (qismlar va fasllar menyusi) mavjud emas.
            # Barcha seriallar Telegramda @asilmediabot orqali yuklanadi
            return await self.run_single_series(item=item, target_bot="asilmediabot")
        return await self.run_single_movie(item=item, target_bot=effective_bot)

    async def run_single_series(self, item: QueueItem, target_bot: str = "asilmediabot") -> bool:
        # Seriallar har doim asilmediabot orqali olinadi
        target_bot = "asilmediabot"

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
        if is_uzmovie and getattr(item, "source", None) == "uzmovi" and num_match and len(num_match.group(0)) <= 6:
            search_query = num_match.group(0)
        elif is_asilmedia and getattr(item, "source", None) == "asilmedia" and num_match and len(num_match.group(0)) <= 6:
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
        season_entries = []
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

                    # Qismlar, fasllar yoki kino sifatlari menyusi chiqishini tezkor kutish
                    def has_card_reply(msgs):
                        return any(nm.buttons and any(any(q in b.text.lower() for q in ["qism", "fasl", "mavsum", "1080", "720", "480"]) or b.text.strip().isdigit() for row in nm.buttons for b in row) for nm in msgs)

                    nm_list = await poll_new_messages(self.client, target_bot, click_id, timeout=8.0, condition=has_card_reply)
                    for nm in nm_list:
                        if nm.buttons:
                            m = nm
                            break

            # Agar bot serial emas, to'g'ridan-to'g'ri film kartasini qaytargan bo'lsa (1080p, 720p, 480p):
            if m.buttons and any(any(q in b.text for q in ["1080", "720", "480"]) for row in m.buttons for b in row):
                logger.info(f"ℹ️ '{item.title}' botda serial emas, film sifatida joylashtirilgan. Kino sikliga yo'naltirilmoqda...")
                item.media_type = "movie"
                return await self.run_single_movie(item=item, target_bot=target_bot)

            # Fasllar (1-fasl, 2-fasl) yoki qismlar tugmalarini aniqlash
            for row_idx, row in enumerate(m.buttons or []):
                for col_idx, btn in enumerate(row):
                    b_lower = btn.text.strip().lower()
                    m_s = re.search(r'(\d+)\s*[-_]?\s*(?:fasl|mavsum|sezon|season)', b_lower)
                    if m_s:
                        season_entries.append((int(m_s.group(1)), row_idx, col_idx, btn.text.strip()))
                    else:
                        m_s2 = re.search(r'(?:fasl|mavsum|sezon|season)\s*(\d+)', b_lower)
                        if m_s2:
                            season_entries.append((int(m_s2.group(1)), row_idx, col_idx, btn.text.strip()))

            if any(b for row in m.buttons for b in row if b.text.strip().isdigit() or "qism" in b.text.lower() or "fasl" in b.text.lower() or "mavsum" in b.text.lower()):
                card_msg = m
                break

        if not card_msg or not card_msg.buttons:
            async for nm in self.client.iter_messages(target_bot, limit=4):
                if nm.buttons and any(any(q in b.text for q in ["1080", "720", "480"]) for row in nm.buttons for b in row):
                    logger.info(f"ℹ️ '{item.title}' botda film sifatida topildi. Kino sikliga yo'naltirilmoqda...")
                    item.media_type = "movie"
                    return await self.run_single_movie(item=item, target_bot=target_bot)
                if nm.buttons and any(b for row in nm.buttons for b in row if b.text.strip().isdigit() or "qism" in b.text.lower() or "fasl" in b.text.lower() or "mavsum" in b.text.lower()):
                    card_msg = nm
                    for row_idx, row in enumerate(nm.buttons):
                        for col_idx, btn in enumerate(row):
                            b_lower = btn.text.strip().lower()
                            m_s = re.search(r'(\d+)\s*[-_]?\s*(?:fasl|mavsum|sezon|season)', b_lower)
                            if m_s and not any(s[0] == int(m_s.group(1)) for s in season_entries):
                                season_entries.append((int(m_s.group(1)), row_idx, col_idx, btn.text.strip()))
                    break

        if not card_msg or not card_msg.buttons:
            # Tekshiramiz: balki botda serial emas, to'g'ridan-to'g'ri kino sifati tugmalari (1080p, 720p, 480p) chiqqandir?
            for m_chk in recent_msgs:
                if m_chk.buttons and any(any(q in b.text for q in ["1080", "720", "480"]) for row in m_chk.buttons for b in row):
                    logger.info(f"ℹ️ '{item.title}' botda serial emas, film sifatida joylashtirilgan. Kino sikliga yo'naltirilmoqda...")
                    item.media_type = "movie"
                    return await self.run_single_movie(item=item, target_bot=target_bot)

            for m in recent_msgs:
                if m.buttons and any("tayyor bo'lganda" in b.text.lower() for row in m.buttons for b in row):
                    err_msg = "Serial hali botga yuklanmagan (Tez kunda / 'Tayyor bo'lganda yuboring')"
                    logger.warning(f"[@{target_bot}] {err_msg}")
                    QueueManager().update_status(item.id, "failed", error_message=err_msg)
                    return False
            logger.warning(f"[@{target_bot}] Serial qismlari yoki fasllari tugmalari topilmadi!")
            QueueManager().update_status(item.id, "failed", error_message=f"[@{target_bot}] Serial tugmalari topilmadi")
            return False

        if season_entries:
            season_entries.sort(key=lambda x: x[0])
            logger.info(f"🎬 Botda {len(season_entries)} ta mavsum topildi: {[s[3] for s in season_entries]}")
        else:
            season_entries = [(1, None, None, "1-Mavsum")]

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

        # 4. Bazada serial va Forum Topic yaratish / tekshirish
        series_id = existing_series_id

        # Qayta dublikat tekshiruvi (boyitilgandan so'ng aniqlangan toza nom va TMDb ID bo'yicha)
        if not series_id:
            sec_dup = await self.dup_checker.check(
                title=title,
                year=year,
                original_title=meta.get("original_title"),
                media_type="series",
                tmdb_id=meta.get("tmdb_id")
            )
            if sec_dup.is_duplicate:
                logger.info(
                    f"ℹ️ Serial (boyitilgandan so'ng) bazada topildi: ID={sec_dup.matched_id} ('{sec_dup.matched_title}'). "
                    f"Yangi serial/topic ochilmaydi, mavjudiga ulanadi."
                )
                series_id = sec_dup.matched_id
        thread_id = None
        target_chat = AUTO_TOPIC_CHAT_ID

        async with async_session_factory() as session:
            series_repo = SeriesRepository(session)
            series_service = SeriesService(repository=series_repo, telegram_api=telegram_client)

            if series_id:
                db_series = await series_service.get_series_by_id(series_id)
                if db_series and db_series.source and db_series.source.topic_id:
                    thread_id = db_series.source.topic_id

                if not thread_id:
                    topic_name = f"🎬 {title} (Serial){year_str}"
                    logger.info(f"ℹ️ Mavjud serial uchun Forum Topic ochilmoqda: '{topic_name}'...")
                    thread_id = await self._create_topic(chat_id=target_chat, title=topic_name)
                    if thread_id and db_series:
                        if db_series.source_id:
                            src = await session.get(SourceModel, db_series.source_id)
                            if src:
                                src.topic_id = thread_id
                                await session.commit()
                        else:
                            src = SourceModel(
                                name=title,
                                type="superguruh",
                                chat_id=int(target_chat) if (isinstance(target_chat, int) or (isinstance(target_chat, str) and target_chat.lstrip('-').isdigit())) else 0,
                                topic_id=int(thread_id)
                            )
                            session.add(src)
                            await session.flush()
                            db_series.source_id = src.id
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
                    chat_id=int(target_chat) if (isinstance(target_chat, int) or (isinstance(target_chat, str) and target_chat.lstrip('-').isdigit())) else 0,
                    topic_id=int(thread_id) if thread_id else None
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
                await session.commit()
                logger.info(f"✅ Serial bazada muvaffaqiyatli yaratildi (Series ID: {series_id})")

        # 5. Har bir mavsum va qismlarni ketma-ket yuklash
        uploaded_count = 0
        storage_chat = STORAGE_CHANNEL_ID

        for s_num, s_r_idx, s_c_idx, s_b_name in season_entries:
            logger.info(f"\n==========================================")
            logger.info(f"📺 MAVSUM {s_num}: '{s_b_name}'")
            logger.info(f"==========================================")

            # Bazada Mavsumni olish yoki yaratish
            season_id = None
            async with async_session_factory() as session:
                series_repo = SeriesRepository(session)
                series_service = SeriesService(repository=series_repo, telegram_api=telegram_client)
                all_seasons = await series_repo.get_seasons_by_series(series_id)
                matched_season = next((s for s in all_seasons if s.season_number == s_num), None)
                if not matched_season:
                    created_season = await series_service.create_season(SeasonCreate(
                        series_id=series_id,
                        season_number=s_num,
                        title=f"{s_num}-Mavsum"
                    ))
                    season_id = created_season.id
                else:
                    season_id = matched_season.id
                await session.commit()

            # Agar mavsum tugmalari mavjud bo'lsa
            if len(season_entries) > 1 or s_r_idx is not None:
                try:
                    latest_card = await self.client.get_messages(target_bot, ids=card_msg.id)
                    if latest_card and latest_card.buttons:
                        card_msg = latest_card

                    # 1. Agar joriy karta mavsum tugmalarini ko'rsatmayotgan bo'lsa (masalan qismlar ko'rinib turgan bo'lsa),
                    # "Ortga / Fasllar" tugmasi orqali mavsumlar ro'yxatiga qaytamiz
                    has_season_buttons = any(
                        re.search(r'\b(?:\d+[-_]?\s*(?:fasl|mavsum)|(?:fasl|mavsum)\s*\d+)\b', b.text.lower())
                        for row in (card_msg.buttons or []) for b in row
                    )
                    if not has_season_buttons:
                        for b_r, b_row in enumerate(card_msg.buttons or []):
                            for b_c, b in enumerate(b_row):
                                if any(w in b.text.lower() for w in ["fasllar", "mavsumlar", "ortga", "orqaga", "◀️", "back"]):
                                    logger.info(f"Mavsumlar menyusiga qaytish bosilmoqda: '{b.text}'...")
                                    await self.safe_click(card_msg, b_r, b_c)
                                    await asyncio.sleep(2.5)
                                    card_msg = await self.client.get_messages(target_bot, ids=card_msg.id)
                                    break

                    # 2. s_num mavsum tugmasini joriy kartadan matn bo'yicha qidiramiz
                    season_btn_pos = None
                    for b_r, b_row in enumerate(card_msg.buttons or []):
                        for b_c, b in enumerate(b_row):
                            b_t = b.text.lower()
                            if f"{s_num}-fasl" in b_t or f"{s_num}-mavsum" in b_t or f"{s_num} fasl" in b_t or f"{s_num} mavsum" in b_t or f"fasl {s_num}" in b_t or f"mavsum {s_num}" in b_t:
                                season_btn_pos = (b_r, b_c, b.text)
                                break
                        if season_btn_pos:
                            break

                    if not season_btn_pos and s_r_idx is not None:
                        season_btn_pos = (s_r_idx, s_c_idx, s_b_name)

                    if season_btn_pos:
                        sr, sc, s_name = season_btn_pos
                        logger.info(f"Fasl tugmasi bosilmoqda: '{s_name}'...")
                        await asyncio.sleep(2.0)
                        _, s_flood = await self.safe_click(card_msg, sr, sc)
                        if s_flood > 0:
                            logger.warning(f"⏳ [@{target_bot}] Fasl bosishda flood ({s_flood}s). Kutilmoqda...")
                            await asyncio.sleep(s_flood)
                            await self.safe_click(card_msg, sr, sc)
                        await asyncio.sleep(2.5)
                        refreshed = await self.client.get_messages(target_bot, ids=card_msg.id)
                        if refreshed and refreshed.buttons:
                            card_msg = refreshed
                except Exception as s_err:
                    logger.debug(f"Fasl tugmasini bosishda xatolik: {s_err}")

            # Ushbu mavsum qismlari tugmalarini yig'ish
            episodes_grid_msg_id = card_msg.id
            episodes_map = {}
            for r_idx, row in enumerate(card_msg.buttons or []):
                for c_idx, btn in enumerate(row):
                    t = btn.text.strip()
                    if t.isdigit():
                        episodes_map[int(t)] = (r_idx, c_idx, t)
                    else:
                        m_num = re.search(r'(\d+)\s*[-_]?\s*qism', t, re.I)
                        if m_num:
                            episodes_map[int(m_num.group(1))] = (r_idx, c_idx, t)

            if not episodes_map:
                logger.warning(f"⚠️ {s_num}-mavsum uchun raqamlangan qism tugmalari topilmadi.")
                continue

            logger.info(f"🎬 {s_num}-mavsumda {len(episodes_map)} ta qism topildi: {sorted(list(episodes_map.keys()))}")
            print(f"  🎬 [{s_num}-mavsum] Jami {len(episodes_map)} ta qism topildi. Yuklash boshlanmoqda...", flush=True)

            # Bazada mavjud qismlarni aniqlash
            existing_eps = set()
            async with async_session_factory() as session:
                series_repo = SeriesRepository(session)
                s_model = await series_repo.get_season_by_id(season_id)
                if s_model and s_model.episodes:
                    for ep in s_model.episodes:
                        if ep.translations:
                            existing_eps.add(ep.episode_number)

            total_eps_in_season = len(episodes_map)

            for ep_num in sorted(episodes_map.keys()):
                if ep_num in existing_eps:
                    logger.info(f"⏭ {s_num}-Mavsum, {ep_num}-qism allaqachon mavjud, o'tkazib yuborildi.")
                    print(f"  ⏭ [{s_num}-mavsum] {ep_num}-qism allaqachon bazada bor, o'tkazib yuborildi.", flush=True)
                    continue

                # Anti-flood: Har bir qism oldidan kamida 3.5 soniya tanaffus
                await asyncio.sleep(3.5)

                try:
                    # Asosiy qismlar kartasini tiklash
                    card_msg = await self.client.get_messages(target_bot, ids=episodes_grid_msg_id)
                    has_numbers = any(b for row in (card_msg.buttons or []) for b in row if b.text.strip().isdigit())
                    if not has_numbers and card_msg and card_msg.buttons:
                        for b_r, b_row in enumerate(card_msg.buttons):
                            for b_c, b in enumerate(b_row):
                                if any(w in b.text.lower() for w in ["qismlar", "ortga", "orqaga", "back"]):
                                    await self.safe_click(card_msg, b_r, b_c)
                                    await asyncio.sleep(2.5)
                                    card_msg = await self.client.get_messages(target_bot, ids=episodes_grid_msg_id)
                                    break
                except Exception as e:
                    logger.debug(f"Qismlar ro'yxatini tiklashda xatolik: {e}")

                # ep_num tugmasini joriy menyudan aniqlash
                target_r_idx, target_c_idx = None, None
                btn_name = str(ep_num)
                for row_idx, row in enumerate(card_msg.buttons or []):
                    for col_idx, btn in enumerate(row):
                        t = btn.text.strip()
                        if t == str(ep_num) or t.startswith(f"{ep_num}-") or t.startswith(f"{ep_num} "):
                            target_r_idx, target_c_idx, btn_name = row_idx, col_idx, btn.text
                            break
                    if target_r_idx is not None:
                        break

                if target_r_idx is None:
                    if ep_num in episodes_map:
                        orig_r, orig_c, orig_name = episodes_map[ep_num]
                        if (
                            card_msg.buttons
                            and orig_r < len(card_msg.buttons)
                            and orig_c < len(card_msg.buttons[orig_r])
                            and card_msg.buttons[orig_r][orig_c].text.strip() == str(ep_num)
                        ):
                            target_r_idx, target_c_idx, btn_name = orig_r, orig_c, orig_name

                if target_r_idx is None:
                    logger.warning(f"⚠️ {s_num}-Mavsum, {ep_num}-qism tugmasi menyuda topilmadi, o'tkazib yuborildi.")
                    continue

                logger.info(f"\n--- 📺 {s_num}-Mavsum, {ep_num}-qism yuklanmoqda ({btn_name}) [{uploaded_count + 1}/{total_eps_in_season}] ---")
                print(f"  📺 [{s_num}-mavsum] {ep_num}-qism yuklanmoqda ({uploaded_count + 1}/{total_eps_in_season})...", flush=True)

                try:
                    ep_video_msg = None

                    # Har bir qism uchun 3 martagacha urinish (anti-flood bilan)
                    for ep_attempt in range(3):
                        click_id = card_msg.id
                        success, click_flood = await self.safe_click(card_msg, target_r_idx, target_c_idx)
                        if click_flood > 0:
                            logger.warning(
                                f"⏳ [@{target_bot}] Anti-flood chegarasi ({click_flood}s). "
                                f"Kutib turamiz ({ep_attempt + 1}/3)..."
                            )
                            print(f"  ⏳ Telegram flood-wait ({click_flood}s). Kutib turamiz...", flush=True)
                            await asyncio.sleep(click_flood)
                            card_msg = await self.client.get_messages(target_bot, ids=episodes_grid_msg_id)
                            continue

                        await asyncio.sleep(2.5)

                        quality_msg = None
                        try:
                            refreshed_card = await self.client.get_messages(target_bot, ids=card_msg.id)
                            if refreshed_card and refreshed_card.buttons:
                                if any(b for row in refreshed_card.buttons for b in row if any(q in b.text.lower() for q in ["720", "1080", "480"])):
                                    quality_msg = refreshed_card
                                    card_msg = refreshed_card
                                    logger.info(f"ℹ️ Sifat tugmalari in-place kartada topildi: {[b.text for r in quality_msg.buttons for b in r]}")
                        except Exception as ref_err:
                            logger.debug(f"Card message yangilanishini tekshirishda xatolik: {ref_err}")

                        if not quality_msg:
                            def is_ep_or_quality(msgs):
                                for nm in msgs:
                                    if is_bot_flood_text(nm.text):
                                        return True
                                    if is_video_message(nm):
                                        return True
                                    if nm.buttons and any(b for row in nm.buttons for b in row if any(q in b.text.lower() for q in ["720", "1080", "480"])):
                                        return True
                                return False

                            ep_reply_msgs = await poll_new_messages(self.client, target_bot, click_id, timeout=8.0, interval=0.35, condition=is_ep_or_quality)
                        else:
                            ep_reply_msgs = []

                        # Flood tekshiruvi:
                        flood_wait = get_flood_wait_seconds(ep_reply_msgs)
                        if flood_wait > 0:
                            logger.warning(
                                f"⏳ [@{target_bot}] Bot xabarida flood chegarasi: 'Biroz sekinroq. Bir daqiqadan so'ng urinib ko'ring.' "
                                f"{flood_wait} soniya kutilmoqda ({ep_attempt + 1}/3)..."
                            )
                            print(f"  ⏳ Bot flood-wait ({flood_wait}s). Kutilmoqda...", flush=True)
                            await asyncio.sleep(flood_wait)
                            card_msg = await self.client.get_messages(target_bot, ids=episodes_grid_msg_id)
                            continue

                        for nm in ep_reply_msgs:
                            if is_video_message(nm) and matches_episode(nm, ep_num, total_eps_in_season):
                                ep_video_msg = nm
                                break
                            if nm.buttons and any(b for row in nm.buttons for b in row if any(q in b.text.lower() for q in ["720", "1080", "480"])):
                                quality_msg = nm
                                break

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
                                await asyncio.sleep(2.0)
                                _, q_flood = await self.safe_click(quality_msg, q_r, q_c)
                                if q_flood > 0:
                                    logger.warning(f"⏳ [@{target_bot}] Sifat tugmasida flood ({q_flood}s)...")
                                    await asyncio.sleep(q_flood)

                                def has_final_video(msgs):
                                    return any(
                                        is_bot_flood_text(vm.text) or is_video_message(vm)
                                        for vm in msgs
                                    )

                                v_list = await poll_new_messages(self.client, target_bot, q_click_id, timeout=18.0, interval=0.4, condition=has_final_video)
                                v_flood = get_flood_wait_seconds(v_list)
                                if v_flood > 0:
                                    logger.warning(f"⏳ [@{target_bot}] Video kutishda flood: {v_flood}s kutilmoqda...")
                                    await asyncio.sleep(v_flood)

                                for vm in v_list:
                                    if is_video_message(vm) and matches_episode(vm, ep_num, total_eps_in_season):
                                        ep_video_msg = vm
                                        break

                        if not ep_video_msg:
                            async for fallback_m in self.client.iter_messages(target_bot, limit=10):
                                if is_video_message(fallback_m) and matches_episode(fallback_m, ep_num, total_eps_in_season):
                                    ep_video_msg = fallback_m
                                    logger.info(f"ℹ️ Zaxiradagi xabarlardan {ep_num}-qism videosi topildi (Msg ID: {ep_video_msg.id})")
                                    break

                        if ep_video_msg:
                            break

                        logger.warning(f"⚠️ {s_num}-Mavsum, {ep_num}-qism ({ep_attempt + 1}/3) urinishda olinmadi, 4 soniyadan so'ng qayta uriniladi...")
                        await asyncio.sleep(4.0)
                        card_msg = await self.client.get_messages(target_bot, ids=episodes_grid_msg_id)

                    if not ep_video_msg:
                        logger.warning(f"❌ {s_num}-Mavsum, {ep_num}-qism videosi botdan qabul qilinmadi!")
                        continue

                    # Topic ichiga yuklash
                    ep_caption = (
                        f"🎬 <b>{html.escape(title)}</b>\n"
                        f"🔢 <b>{s_num}-Mavsum, {ep_num}-Qism</b>"
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

                    # Storage kanalga nusxalash
                    storage_caption = (
                        f"🎬 <b>{html.escape(title)}</b>\n"
                        f"🔢 <b>{s_num}-Mavsum, {ep_num}-Qism</b>\n"
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
                    logger.info(f"✅ {s_num}-Mavsum, {ep_num}-qism to'liq yuklandi va bazaga bog'landi! (Storage Msg: {storage_msg.id})")
                    print(f"  ✅ [{s_num}-mavsum] {ep_num}-qism saqlandi va ulandi ({uploaded_count}/{total_eps_in_season})", flush=True)

                    # Navbat statusini yangilash
                    try:
                        QueueManager().update_status(
                            item.id,
                            "in_progress",
                            downloaded_episodes=uploaded_count,
                            episodes_count=total_eps_in_season
                        )
                    except Exception:
                        pass

                    # Keyingi qism uchun qismlar ro'yxatiga qaytish
                    try:
                        latest_card = await self.client.get_messages(target_bot, ids=episodes_grid_msg_id)
                        if latest_card and latest_card.buttons:
                            for b_r, b_row in enumerate(latest_card.buttons):
                                for b_c, b_btn in enumerate(b_row):
                                    if any(w in b_btn.text.lower() for w in ["qismlar", "orqaga", "ortga"]):
                                        await self.safe_click(latest_card, b_r, b_c)
                                        await asyncio.sleep(2.0)
                                        card_msg = await self.client.get_messages(target_bot, ids=episodes_grid_msg_id)
                                        break
                    except Exception:
                        pass

                    await asyncio.sleep(3.5)
                except Exception as ep_err:
                    logger.error(f"❌ {ep_num}-qismni yuklashda xatolik: {ep_err}")
                    print(f"  ❌ [{s_num}-mavsum] {ep_num}-qismda xatolik: {ep_err}", flush=True)
                    await asyncio.sleep(3.5)

            # Agar keyingi mavsum mavjud bo'lsa, mavsumlar menyusiga qaytish
            if len(season_entries) > 1 and s_num != season_entries[-1][0]:
                try:
                    latest_card = await self.client.get_messages(target_bot, ids=card_msg.id)
                    if latest_card and latest_card.buttons:
                        for b_r, b_row in enumerate(latest_card.buttons):
                            for b_c, b_btn in enumerate(b_row):
                                if "fasl" in b_btn.text.lower() or "mavsum" in b_btn.text.lower() or "orqaga" in b_btn.text.lower():
                                    await latest_card.click(b_r, b_c)
                                    await asyncio.sleep(1.0)
                                    card_msg = await self.client.get_messages(target_bot, ids=card_msg.id)
                                    break
                except Exception:
                    pass

        if uploaded_count == 0 and not existing_series_id and series_id:
            logger.warning(f"⚠️ Serialga birorta ham qism yuklanmadi. Baza toza saqlanishi uchun Serial (ID: {series_id}) o'chirilmoqda...")
            try:
                from sqlalchemy import text
                async with async_session_factory() as cleanup_session:
                    await cleanup_session.execute(text("DELETE FROM series_category WHERE series_id = :sid"), {"sid": series_id})
                    await cleanup_session.execute(text("DELETE FROM page_series WHERE series_id = :sid"), {"sid": series_id})
                    await cleanup_session.execute(text("DELETE FROM seasons WHERE series_id = :sid"), {"sid": series_id})
                    await cleanup_session.execute(text("DELETE FROM series WHERE id = :sid"), {"sid": series_id})
                    await cleanup_session.commit()
                logger.info(f"🧹 Chala qolgan serial (ID: {series_id}) tozalandi.")
            except Exception as se_err:
                logger.warning(f"Chala serialni tozalashda xatolik: {se_err}")

        logger.info(f"\n🎉 Serial yakunlandi: {title} | {uploaded_count} ta yangi qism yuklandi.")
        print(f"  🎉 Serial yakunlandi: {title} | {uploaded_count} ta yangi qism yuklandi.", flush=True)
        return uploaded_count > 0

    async def run_single_movie(self, item: QueueItem, target_bot: str = "asilmediabot") -> bool:
        # Agar item manbasi boshqa bot bo'lsa, mos botga to'g'rilash
        if getattr(item, "source", None) == "asilmedia":
            target_bot = "asilmediabot"
        elif getattr(item, "source", None) == "uzmovi":
            target_bot = "UzmovieTV_Bot"

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
        print(f"  🔍 '{item.title}' bo'yicha @{target_bot} botidan video qidirilmoqda...", flush=True)
        video_msg = await self._fetch_video(item=item, target_bot=target_bot)
        if not video_msg:
            # Agar bot serial tugmalarini qaytargan bo'lsa, avtomatik serial deb hisoblab serial siklini bajaramiz
            if self._last_card_msg and self._last_card_msg.buttons:
                has_eps = any(
                    b for row in self._last_card_msg.buttons for b in row
                    if b.text.strip().isdigit() or "qism" in b.text.lower() or "fasl" in b.text.lower() or "mavsum" in b.text.lower()
                )
                if has_eps:
                    logger.info(f"ℹ️ '{item.title}' aslida serial ekanligi aniqlandi! Serial sikliga yo'naltirilmoqda...")
                    item.media_type = "series"
                    return await self.run_single_series(item=item, target_bot=target_bot)

            if getattr(self, "_last_unreleased_notice", None):
                msg = self._last_unreleased_notice
                self._last_unreleased_notice = None
                QueueManager().update_status(item.id, "failed", error_message=msg)
                return False

            logger.warning(f"❌ '{item.title}' bo'yicha @{target_bot} dan video olinmadi.")
            QueueManager().update_status(item.id, "failed", error_message=f"[@{target_bot}] dan video olinmadi")
            return False

        print(f"  📥 '{item.title}' videosi botdan qabul qilindi. AI va Topic jarayoni...", flush=True)
        return await self._process_pipeline(item=item, video_msg=video_msg, target_bot=target_bot, card_msg=self._last_card_msg)

    async def run_kawaii_anime(self, item: QueueItem, max_episodes: Optional[int] = None) -> bool:
        """
        Kawaii.uz animesi bo'yicha to'liq moderator sikli:
        @kawaii_uz_bot orqali kino va ko'p qismli anime seriallarni yuklash,
        Topic ochish, Storage kanalga saqlash va websayt bazasiga ulash.
        """
        target_bot = "kawaii_uz_bot"
        logger.info("\n" + "="*55)
        logger.info(f"🎌 KAWAII ANIME MODERATOR SIKLI: '{item.title}' ({item.year or 'Noma\'lum'}) | BOT: @{target_bot}")
        logger.info("="*55)
        print(f"\n🚀 [KAWAII] '{item.title}' ({item.year or 'Noma\'lum'}) yuklash boshlanmoqda...", flush=True)

        # 1. Slugni aniqlash
        slug = item.id.replace("kawaii_", "").strip() if item.id.startswith("kawaii_") else ""
        if not slug and item.url and "/anime/" in item.url:
            slug = item.url.split("/anime/")[-1].strip().strip("/")
        if not slug:
            slug = item.id.strip()

        # 2. Dublikat tekshiruvi (har ikkala jadval bo'yicha)
        dup_check = await self.dup_checker.check(
            title=item.title,
            year=item.year,
            original_title=item.original_title,
            media_type=None
        )
        if dup_check.is_duplicate:
            if dup_check.matched_type == "movie":
                logger.info(f"ℹ️ Anime film bazada allaqachon mavjud: ID={dup_check.matched_id} ('{dup_check.matched_title}'). O'tkazib yuborildi.")
                print(f"ℹ️ [KAWAII] '{item.title}' bazada film sifatida allaqachon mavjud, o'tkazib yuborildi.", flush=True)
                QueueManager().update_status(item.id, "already_exists")
                return True
            elif dup_check.matched_type == "series" and not getattr(dup_check, "is_incomplete", False):
                logger.info(f"ℹ️ Anime serial bazada to'liq mavjud: ID={dup_check.matched_id} ('{dup_check.matched_title}'). O'tkazib yuborildi.")
                print(f"ℹ️ [KAWAII] '{item.title}' bazada to'liq serial sifatida allaqachon mavjud, o'tkazib yuborildi.", flush=True)
                QueueManager().update_status(item.id, "already_exists")
                return True

        # 3. @kawaii_uz_bot ga so'rov yuborish
        req_cmd = f"/start a-{slug}"
        logger.info(f"[@{target_bot}] botiga so'rov: '{req_cmd}'...")
        sent = await self.client.send_message(target_bot, req_cmd)

        card_msgs = await poll_new_messages(
            self.client,
            target_bot,
            sent.id,
            timeout=10.0,
            interval=0.35,
            condition=lambda msgs: any(m.buttons for m in msgs)
        )
        if not card_msgs:
            logger.error(f"❌ [@{target_bot}] Bot javob bermadi yoki kartada tugmalar yo'q.")
            QueueManager().update_status(item.id, "failed", error_message="Bot javob bermadi")
            return False

        card_msg = card_msgs[0]
        # Homiy tekshiruvi (agar bot obuna bo'lishni so'rasa avtomatik obuna bo'lish):
        unlocked = await self.handle_sponsor_lock(target_bot, card_msg)
        if unlocked:
            card_msg = unlocked
        card_text = card_msg.text or ""

        # Tugmalardan "Tomosha qilish" ni topish
        watch_btn_coords = None
        for r_idx, row in enumerate(card_msg.buttons or []):
            for c_idx, btn in enumerate(row):
                if any(w in btn.text.lower() for w in ["tomosha qilish", "tomosha"]):
                    watch_btn_coords = (r_idx, c_idx)
                    break
            if watch_btn_coords:
                break

        if not watch_btn_coords:
            logger.error(f"❌ [@{target_bot}] 'Tomosha qilish' tugmasi topilmadi.")
            QueueManager().update_status(item.id, "failed", error_message="'Tomosha qilish' tugmasi topilmadi")
            return False

        # Metadata boyitish (AI + TMDb)
        meta = await enrich_movie_smart(
            raw_title=item.title,
            year=item.year,
            original_title=item.original_title,
            source_poster=item.poster_url,
            caption=card_text,
            media_type=item.media_type
        )
        title = meta.get("title") or item.title
        year = meta.get("year") or item.year
        target_chat = AUTO_TOPIC_CHAT_ID or STORAGE_CHANNEL_ID
        storage_chat = STORAGE_CHANNEL_ID

        # 5. "Tomosha qilish" tugmasini bosish
        logger.info(f"[@{target_bot}] 'Tomosha qilish' tugmasi bosilmoqda...")
        click_id = card_msg.id
        await self.safe_click(card_msg, watch_btn_coords[0], watch_btn_coords[1])
        await asyncio.sleep(2.0)

        # Kartani yangilangan holatini olish
        updated_card = await self.client.get_messages(target_bot, ids=click_id)
        if updated_card:
            card_msg = updated_card

        # Tekshiramiz: bu kino (1 qism)mi yoki ko'p qismli serialmi?
        has_video_now = bool(card_msg.media and getattr(card_msg.media, "document", None) and getattr(card_msg.media, "video", False))

        ep_buttons = []
        for r_i, row in enumerate(card_msg.buttons or []):
            for c_i, btn in enumerate(row):
                m_ep = re.search(r'(\d+)\s*ep\b', btn.text, re.I)
                if m_ep:
                    ep_buttons.append((int(m_ep.group(1)), r_i, c_i, btn.text))

        # Agar botda 1 tadan ortiq ep tugmasi bo'lsa - bu qat'iy serial!
        is_single_movie = (len(ep_buttons) <= 1) and (
            item.media_type == "movie" or (has_video_now and "1 / 1" in card_text) or "film" in title.lower()
        )

        # A) KINO SIKLI (1 qism)
        if is_single_movie:
            logger.info(f"🎬 '{title}' yagona film/kino sifatida aniqlandi. Dublikat tekshirilmoqda...")
            movie_dup = await self.dup_checker.check(
                title=title,
                year=year,
                original_title=meta.get("original_title") or item.original_title,
                media_type="movie",
                tmdb_id=meta.get("tmdb_id")
            )
            if movie_dup.is_duplicate:
                logger.info(f"ℹ️ Anime film bazada allaqachon mavjud: ID={movie_dup.matched_id} ('{movie_dup.matched_title}'). O'tkazib yuborildi.")
                print(f"ℹ️ [KAWAII] '{title}' bazada allaqachon mavjud (ID: {movie_dup.matched_id}), o'tkazib yuborildi.", flush=True)
                QueueManager().update_status(item.id, "already_exists")
                return True

            print(f"🎬 [KAWAII] '{title}' film sifatida yuklanmoqda...", flush=True)

            video_msg = None
            if has_video_now:
                video_msg = card_msg
            elif ep_buttons:
                ep_r, ep_c = ep_buttons[0][1], ep_buttons[0][2]
                await self.safe_click(card_msg, ep_r, ep_c)
                await asyncio.sleep(2.5)
                v_card = await self.client.get_messages(target_bot, ids=click_id)
                if v_card and v_card.media and getattr(v_card.media, "video", False):
                    video_msg = v_card

            if not video_msg:
                logger.error(f"❌ '{title}' video xabari topilmadi!")
                QueueManager().update_status(item.id, "failed", error_message="Video topilmadi")
                return False

            # Topic yaratish
            thread_id = None
            if AUTO_TOPIC_CHAT_ID:
                try:
                    res_topic = await self.client(CreateForumTopicRequest(
                        peer=AUTO_TOPIC_CHAT_ID,
                        title=f"{title[:100]} ({year or ''})".strip(),
                        icon_color=0x6FB9F0
                    ))
                    thread_id = res_topic.updates[0].id if hasattr(res_topic, 'updates') and res_topic.updates else getattr(res_topic, 'id', None)
                except Exception as top_err:
                    logger.warning(f"Topic ochishda xatolik: {top_err}")

            # Darhol topic ichiga banner/poster yuborish (topic bo'm-bo'sh turmasligi uchun):
            if thread_id and AUTO_TOPIC_CHAT_ID:
                rating_str = f"⭐ <b>Reyting:</b> {meta.get('imdb_rating') or meta.get('tmdb_rating') or '7.0'}/10\n" if (meta.get('imdb_rating') or meta.get('tmdb_rating')) else ""
                director_str = f"🎬 <b>Rejissyor:</b> {html.escape(meta['director'])}\n" if meta.get("director") else ""
                cast_str = f"👥 <b>Aktyorlar:</b> {html.escape(meta['cast'][:120])}...\n" if meta.get("cast") else ""
                year_str = f" ({year})" if year else ""
                welcome_text = (
                    f"🎬 <b>{html.escape(title)}</b> (Anime film){year_str}\n"
                    f"🎭 <b>Janr:</b> {html.escape(meta.get('genres') or 'Anime film')}\n"
                    f"{rating_str}{director_str}{cast_str}"
                    f"\n📝 <b>Tavsif:</b>\n<i>{html.escape(meta.get('description') or '')}</i>\n\n"
                    f"⏳ <i>Video yuklanmoqda, kuting...</i>"
                )
                poster_to_send = meta.get("poster_url") or item.poster_url
                if poster_to_send:
                    try:
                        await self.client.send_file(
                            AUTO_TOPIC_CHAT_ID,
                            file=poster_to_send,
                            caption=welcome_text,
                            reply_to=thread_id,
                            parse_mode="html"
                        )
                    except Exception:
                        await self.client.send_message(AUTO_TOPIC_CHAT_ID, message=welcome_text, reply_to=thread_id, parse_mode="html")
                else:
                    await self.client.send_message(AUTO_TOPIC_CHAT_ID, message=welcome_text, reply_to=thread_id, parse_mode="html")

            # Topicga yuklash
            topic_caption = (
                f"🎬 <b>{html.escape(title)}</b>\n"
                f"🔑 <b>Kodi:</b> <code>{slug}</code>\n"
                + (f"📅 <b>Yili:</b> {year}\n" if year else "")
            )
            topic_video_msg = await self._upload_video_to_chat(
                video_msg=video_msg,
                target_chat=target_chat,
                reply_to=thread_id,
                caption=topic_caption
            )
            if not topic_video_msg:
                topic_video_msg = video_msg

            # Storage kanalga nusxalash
            storage_caption = (
                f"🍿 <b>{html.escape(title)}</b>\n"
                f"🔑 <b>Kodi:</b> <code>{slug}</code>\n"
                + (f"📅 <b>Yili:</b> {year}\n" if year else "")
            )
            storage_msg = await self._upload_video_to_chat(
                video_msg=topic_video_msg,
                target_chat=storage_chat,
                reply_to=None,
                caption=storage_caption
            )
            if not storage_msg:
                storage_msg = topic_video_msg

            # DB ga yozish
            bot_file_id = None
            try:
                from telethon.utils import pack_bot_file_id
                if storage_msg and storage_msg.media:
                    bot_file_id = pack_bot_file_id(storage_msg.media)
            except Exception:
                pass

            async with async_session_factory() as session:
                repo = MovieRepositoryImpl(session)
                service = MovieService(repo)
                created_movie = await service.create_movie(
                    title=title,
                    original_title=meta.get("original_title") or item.original_title,
                    description=meta.get("description"),
                    imdb_rating=meta.get("imdb_rating"),
                    tmdb_rating=meta.get("tmdb_rating"),
                    tmdb_id=meta.get("tmdb_id"),
                    genres=meta.get("genres"),
                    cast=meta.get("cast"),
                    director=meta.get("director"),
                    release_year=year,
                    runtime=meta.get("runtime"),
                    poster_url=meta.get("poster_url") or item.poster_url,
                    trailer_url=meta.get("trailer_url"),
                    category_ids=meta.get("category_ids")
                )
                movie_id = created_movie.id
                await service.link_movie_video_from_message(
                    movie_id=movie_id,
                    message_id=storage_msg.id,
                    language="Asosiy",
                    telegram_file_id=bot_file_id
                )
                await session.commit()

            try:
                await delete_cache_pattern("cache:movies:*")
            except Exception:
                pass

            QueueManager().update_status(item.id, "completed")
            print(f"✅ [KAWAII] Film muvaffaqiyatli saqlandi va websaytga ulandi! (ID: {movie_id})", flush=True)
            return True

        # B) KO'P QISMLI SERIAL SIKLI
        logger.info(f"📺 '{title}' serial sifatida yuklanmoqda...")
        print(f"📺 [KAWAII] '{title}' serial sifatida yuklanmoqda...", flush=True)

        series_id = None
        season_id = None
        thread_id = None
        newly_created_series = False

        async with async_session_factory() as session:
            series_repo = SeriesRepository(session)
            series_service = SeriesService(repository=series_repo, telegram_api=telegram_client)

            existing_series = await series_repo.get_series_by_title_and_year(title, year)
            if not existing_series:
                sec_dup = await self.dup_checker.check(
                    title=title,
                    year=year,
                    original_title=meta.get("original_title"),
                    media_type="series",
                    tmdb_id=meta.get("tmdb_id")
                )
                if sec_dup.is_duplicate and sec_dup.matched_id:
                    existing_series = await series_repo.get_series_by_id(sec_dup.matched_id)

            if existing_series:
                series_id = existing_series.id
                if existing_series.source and existing_series.source.topic_id:
                    thread_id = existing_series.source.topic_id
                    logger.info(f"ℹ️ Mavjud serialning Topic ID si ishlatiladi: {thread_id}")

            if not existing_series:
                source = SourceModel(
                    name=title,
                    type="superguruh",
                    chat_id=int(target_chat) if (isinstance(target_chat, int) or (isinstance(target_chat, str) and target_chat.lstrip('-').isdigit())) else 0,
                    topic_id=None
                )
                session.add(source)
                await session.flush()

                series_data = SeriesCreate(
                    title=title,
                    description=meta.get("description"),
                    poster_url=meta.get("poster_url") or item.poster_url,
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
                newly_created_series = True
            else:
                newly_created_series = False

            all_seasons = await series_repo.get_seasons_by_series(series_id)
            matched_season = next((s for s in all_seasons if s.season_number == 1), None)
            if not matched_season:
                created_season = await series_service.create_season(SeasonCreate(
                    series_id=series_id,
                    season_number=1,
                    title="1-Mavsum"
                ))
                season_id = created_season.id
            else:
                season_id = matched_season.id
            await session.commit()

        existing_eps = set()
        async with async_session_factory() as session:
            series_repo = SeriesRepository(session)
            s_model = await series_repo.get_season_by_id(season_id)
            if s_model and s_model.episodes:
                for ep in s_model.episodes:
                    if ep.translations:
                        existing_eps.add(ep.episode_number)

        total_ep_count = item.episodes_count or len(ep_buttons) or 12
        current_ep = 1
        downloaded_in_session = 0

        while current_ep <= total_ep_count:
            if max_episodes and downloaded_in_session >= max_episodes:
                logger.info(f"🛑 Belgilangan maksimal qismlar soniga ({max_episodes}) yetildi. Sikl to'xtatilmoqda.")
                print(f"🛑 Belgilangan maksimal qismlar soniga ({max_episodes}) yetildi.", flush=True)
                break

            if current_ep in existing_eps:
                logger.info(f"⏭ {current_ep}-qism allaqachon mavjud, o'tkazib yuborildi.")
                current_ep += 1
                continue

            await asyncio.sleep(2.5)

            card_msg = await self.client.get_messages(target_bot, ids=click_id)
            target_btn = None
            next_page_btn = None

            for r_i, row in enumerate(card_msg.buttons or []):
                for c_i, btn in enumerate(row):
                    b_t = btn.text.strip().lower()
                    m_ep = re.search(r'(\d+)\s*ep\b', b_t)
                    if m_ep and int(m_ep.group(1)) == current_ep:
                        target_btn = (r_i, c_i, btn)
                    if "keyingi" in b_t or "➡️" in b_t:
                        next_page_btn = (r_i, c_i, btn)

            if not target_btn and next_page_btn:
                logger.info(f"📄 Keyingi qismlar sahifasiga o'tilmoqda ({next_page_btn[2].text})...")
                await self.safe_click(card_msg, next_page_btn[0], next_page_btn[1])
                await asyncio.sleep(2.0)
                continue

            if not target_btn:
                logger.warning(f"⚠️ {current_ep}-qism tugmasi topilmadi. Serial yakunlangan bo'lishi mumkin.")
                break

            logger.info(f"▶️ {current_ep}-qism yuklanmoqda ({target_btn[2].text})...")
            print(f"  ▶️ [KAWAII] {current_ep}-qism yuklanmoqda...", flush=True)

            v_msg = None
            # 1-qism videosi "Tomosha qilish" bosilishi bilanoq bot tomonidan kartaga biriktirib berilgan bo'ladi!
            if current_ep == 1 and is_video_message(card_msg):
                v_msg = card_msg
            else:
                prev_doc = getattr(getattr(card_msg, "media", None), "document", None)
                prev_doc_id = prev_doc.id if prev_doc else None

                await self.safe_click(card_msg, target_btn[0], target_btn[1])

                # Kawaii bot yangi xabar yubormaydi, mavjud xabarni (click_id) in-place tahrirlab yangi video qo'yadi:
                for _ in range(12):
                    await asyncio.sleep(1.0)
                    fresh_m = await self.client.get_messages(target_bot, ids=click_id)
                    if fresh_m and fresh_m.media:
                        cur_doc = getattr(fresh_m.media, "document", None)
                        has_ep_text = bool(fresh_m.text and re.search(rf'epizod\s*\**\s*{current_ep}\b', fresh_m.text, re.I))
                        if cur_doc and (cur_doc.id != prev_doc_id or has_ep_text):
                            v_msg = fresh_m
                            card_msg = fresh_m
                            logger.info(f"✅ In-place edit aniqlandi: {current_ep}-qism videosi yangilandi (Doc ID: {cur_doc.id})")
                            break

                if not v_msg:
                    fresh_fallback = await self.client.get_messages(target_bot, ids=click_id)
                    if is_video_message(fresh_fallback):
                        v_msg = fresh_fallback
                        card_msg = fresh_fallback

            if not is_video_message(v_msg):
                logger.warning(f"❌ {current_ep}-qism videosi qabul qilinmadi, keyingisiga o'tilmoqda.")
                current_ep += 1
                continue

            # Faqat video muvaffaqiyatli qabul qilingandagina yangi Forum Topic ochiladi:
            if not thread_id and AUTO_TOPIC_CHAT_ID:
                try:
                    res_topic = await self.client(CreateForumTopicRequest(
                        peer=AUTO_TOPIC_CHAT_ID,
                        title=f"📺 {title[:95]} ({year or ''})".strip(),
                        icon_color=0x6FB9F0
                    ))
                    thread_id = res_topic.updates[0].id if hasattr(res_topic, 'updates') and res_topic.updates else getattr(res_topic, 'id', None)
                    if thread_id:
                        logger.info(f"✅ Yangi Forum Topic ochildi (ID: {thread_id})")
                        rating_str = f"⭐ <b>Reyting:</b> {meta.get('imdb_rating') or meta.get('tmdb_rating') or '7.0'}/10\n" if (meta.get('imdb_rating') or meta.get('tmdb_rating')) else ""
                        director_str = f"🎬 <b>Rejissyor:</b> {html.escape(meta['director'])}\n" if meta.get("director") else ""
                        cast_str = f"👥 <b>Aktyorlar:</b> {html.escape(meta['cast'][:120])}...\n" if meta.get("cast") else ""
                        year_str = f" ({year})" if year else ""
                        welcome_text = (
                            f"📺 <b>{html.escape(title)}</b> (Anime Serial){year_str}\n"
                            f"🎭 <b>Janr:</b> {html.escape(meta.get('genres') or 'Anime')}\n"
                            f"{rating_str}{director_str}{cast_str}"
                            f"\n📝 <b>Tavsif:</b>\n<i>{html.escape(meta.get('description') or '')}</i>\n\n"
                            f"⬇️ <i>Serial qismlari shu yerga yuklanmoqda...</i>"
                        )
                        poster_to_send = meta.get("poster_url") or item.poster_url
                        if poster_to_send:
                            try:
                                await self.client.send_file(AUTO_TOPIC_CHAT_ID, file=poster_to_send, caption=welcome_text, reply_to=thread_id, parse_mode="html")
                            except Exception:
                                await self.client.send_message(AUTO_TOPIC_CHAT_ID, message=welcome_text, reply_to=thread_id, parse_mode="html")
                        else:
                            await self.client.send_message(AUTO_TOPIC_CHAT_ID, message=welcome_text, reply_to=thread_id, parse_mode="html")

                        # Series source topic_id sini yangilaymiz
                        if series_id:
                            async with async_session_factory() as update_session:
                                upd_s = await update_session.get(SeriesModel, series_id)
                                if upd_s and upd_s.source_id:
                                    upd_src = await update_session.get(SourceModel, upd_s.source_id)
                                    if upd_src:
                                        upd_src.topic_id = int(thread_id)
                                        await update_session.commit()
                except Exception as top_err:
                    logger.warning(f"Topic ochishda xatolik: {top_err}")

            ep_caption = (
                f"🎬 <b>{html.escape(title)}</b>\n"
                f"🔢 <b>{current_ep}-Qism</b>"
            )
            topic_msg = await self._upload_video_to_chat(
                video_msg=v_msg,
                target_chat=target_chat,
                reply_to=thread_id,
                caption=ep_caption
            )
            if not topic_msg:
                topic_msg = v_msg

            storage_caption = (
                f"🎬 <b>{html.escape(title)}</b>\n"
                f"🔢 <b>{current_ep}-Qism</b>\n"
                + (f"📅 <b>Yili:</b> {year}\n" if year else "")
            )
            storage_msg = await self._upload_video_to_chat(
                video_msg=topic_msg,
                target_chat=storage_chat,
                reply_to=None,
                caption=storage_caption
            )
            if not storage_msg:
                storage_msg = topic_msg

            async with async_session_factory() as session:
                series_repo = SeriesRepository(session)
                series_service = SeriesService(repository=series_repo, telegram_api=telegram_client)
                ep_entity = await series_service.create_episode(EpisodeCreate(
                    season_id=season_id,
                    episode_number=current_ep,
                    title=f"{current_ep}-qism"
                ))
                ep_id = ep_entity.id

                ep_bot_file_id = None
                try:
                    from telethon.utils import pack_bot_file_id
                    if storage_msg and storage_msg.media:
                        ep_bot_file_id = pack_bot_file_id(storage_msg.media)
                except Exception:
                    pass

                # Bot kartasidan ovoz jamoasini aniqlash (masalan: 🎙 Anizzers)
                raw_caption = (card_msg.text or (v_msg.text if v_msg else "")) or ""
                voice_match = re.search(r'🎙\s*([^•\n\r]+)', raw_caption)
                voiceover_team = voice_match.group(1).strip() if voice_match else "Kawaii Uz"

                await series_repo.add_episode_translation(
                    episode_id=ep_id,
                    language="Asosiy",
                    telegram_file_id=ep_bot_file_id,
                    storage_channel_message_id=storage_msg.id
                )
                await session.commit()

            downloaded_in_session += 1
            item.downloaded_episodes = downloaded_in_session
            print(f"  ✅ [KAWAII] {current_ep}-qism saqlandi!", flush=True)

            try:
                QueueManager().update_status(
                    item.id,
                    "completed" if (downloaded_in_session >= total_ep_count and not max_episodes) else "in_progress",
                    downloaded_episodes=downloaded_in_session,
                    episodes_count=total_ep_count
                )
            except Exception:
                pass

            if max_episodes and downloaded_in_session >= max_episodes:
                logger.info(f"🛑 Belgilangan maksimal qismlar soniga ({max_episodes}) yetildi. Sikl yakunlandi.")
                print(f"🛑 Belgilangan maksimal qismlar soniga ({max_episodes}) yetildi.", flush=True)
                current_ep += 1
                break

            current_ep += 1

        try:
            await delete_cache_pattern("cache:series:*")
        except Exception:
            pass

        if downloaded_in_session == 0:
            if thread_id and AUTO_TOPIC_CHAT_ID and newly_created_series:
                try:
                    from telethon.tl.functions.messages import DeleteTopicHistoryRequest
                    peer_del = await self.client.get_input_entity(AUTO_TOPIC_CHAT_ID)
                    await self.client(DeleteTopicHistoryRequest(peer=peer_del, top_msg_id=thread_id))
                    logger.info(f"🧹 Bo'sh qolgan topic Telegramdan o'chirildi: {thread_id}")
                except Exception as del_top_err:
                    logger.warning(f"Bo'sh topicni o'chirishda xatolik: {del_top_err}")

            if newly_created_series and series_id:
                try:
                    from sqlalchemy import text
                    async with async_session_factory() as cleanup_session:
                        await cleanup_session.execute(text("DELETE FROM series_category WHERE series_id = :sid"), {"sid": series_id})
                        await cleanup_session.execute(text("DELETE FROM page_series WHERE series_id = :sid"), {"sid": series_id})
                        await cleanup_session.execute(text("DELETE FROM seasons WHERE series_id = :sid"), {"sid": series_id})
                        await cleanup_session.execute(text("DELETE FROM series WHERE id = :sid"), {"sid": series_id})
                        await cleanup_session.commit()
                    logger.info(f"🧹 Chala serial (ID: {series_id}) tozalandi.")
                except Exception as se_err:
                    logger.warning(f"Chala serialni tozalashda xatolik: {se_err}")

            QueueManager().update_status(item.id, "failed", error_message="Birorta ham qism yuklanmadi")
            print(f"⚠️ [KAWAII] '{title}': Birorta ham qism yuklanmadi, bo'sh topic tozalandi.", flush=True)
            return False

        final_status = "completed" if (downloaded_in_session >= total_ep_count and not max_episodes) else "in_progress"
        QueueManager().update_status(
            item.id,
            final_status,
            downloaded_episodes=downloaded_in_session,
            episodes_count=total_ep_count
        )
        print(f"🎉 [KAWAII] Serial yakunlandi! Jami {downloaded_in_session} ta qism saqlandi (Status: {final_status}).", flush=True)
        return True

    async def run_by_code(self, code: str, target_bot: str = "asilmediabot", max_episodes: Optional[int] = None) -> bool:
        clean_code = str(code).strip()
        logger.info("\n" + "="*55)
        logger.info(f"🎬 MODERATOR SIKLI: KOD #{clean_code} | BOT: @{target_bot}")
        logger.info("="*55)

        # 0. Navbatdan ushbu kodga tegishli item bormi tekshiramiz
        qm = QueueManager()
        queued_item = qm.get_item_by_code(clean_code)

        # Kawaii bot tekshiruvi
        if target_bot in ("kawaii", "kawaii_uz_bot") or (queued_item and getattr(queued_item, "source", None) == "kawaii"):
            if queued_item:
                return await self.run_kawaii_anime(item=queued_item, max_episodes=max_episodes)
            dummy = QueueItem(
                id=f"kawaii_{clean_code}",
                source="kawaii",
                title=f"Kawaii Anime {clean_code}",
                original_title=None,
                year=None,
                media_type="series",
                url=f"https://bot.kawaii.uz/anime/{clean_code}"
            )
            return await self.run_kawaii_anime(item=dummy, max_episodes=max_episodes)

        if queued_item and queued_item.media_type == "series":
            logger.info(f"ℹ️ Kod #{clean_code} navbatda serial sifatida qayd etilgan ('{queued_item.title}'). Serial sikliga yo'naltirilmoqda...")
            return await self.run_single_series(item=queued_item, target_bot=target_bot)

        video_msg = await self._fetch_video(code=clean_code, target_bot=target_bot)
        if not video_msg:
            if self._last_card_msg and self._last_card_msg.buttons:
                has_eps = any(
                    b for row in self._last_card_msg.buttons for b in row
                    if b.text.strip().isdigit() or "qism" in b.text.lower() or "fasl" in b.text.lower() or "mavsum" in b.text.lower()
                )
                if has_eps:
                    logger.info(f"ℹ️ Kod #{clean_code} bot tomonidan serial sifatida aniqlandi. Serial sikliga yo'naltirilmoqda...")
                    raw_text = self._last_card_msg.text or ""
                    caption_title_m = re.search(r'🎬\s*([^\n\r–]+)', raw_text)
                    raw_title = caption_title_m.group(1).strip() if caption_title_m else f"Serial #{clean_code}"
                    raw_title = clean_movie_title(raw_title)

                    caption_year = None
                    year_m = re.search(r'Yil:\s*(\d{4})', raw_text, re.I)
                    if year_m:
                        caption_year = int(year_m.group(1))

                    series_item = queued_item or QueueItem(
                        id=f"{target_bot.lower()}_{clean_code}",
                        source="asilmedia" if "asil" in target_bot.lower() else "uzmovi",
                        title=raw_title,
                        year=caption_year,
                        media_type="series"
                    )
                    return await self.run_single_series(item=series_item, target_bot=target_bot)

            logger.warning(f"❌ Kod #{clean_code} bo'yicha botdan video olinmadi.")
            return False

        caption = video_msg.text or ""
        caption_title_m = re.search(r'🎬\s*([^\n\r–]+)', caption)
        raw_title = caption_title_m.group(1).strip() if caption_title_m else f"Film #{clean_code}"
        raw_title = clean_movie_title(raw_title)

        caption_year = None
        year_m = re.search(r'Yil:\s*(\d{4})', caption, re.I)
        if year_m:
            caption_year = int(year_m.group(1))
        else:
            year_fallback = re.search(r'\b(19\d{2}|20\d{2})\b', caption)
            if year_fallback:
                caption_year = int(year_fallback.group(1))

        item = queued_item or QueueItem(
            id=f"{target_bot.lower()}_{clean_code}",
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

        # Qayta dublikat tekshiruvi (boyitilgandan so'ng aniqlangan toza nom va TMDb ID bo'yicha)
        sec_dup = await self.dup_checker.check(
            title=title,
            year=year,
            original_title=meta.get("original_title"),
            media_type="movie",
            tmdb_id=meta.get("tmdb_id")
        )
        if sec_dup.is_duplicate:
            logger.warning(
                f"⚠️ [DUBLIKAT (boyitishdan so'ng)] '{title}' bazada mavjud: "
                f"[{sec_dup.matched_type}] '{sec_dup.matched_title}' (ID: {sec_dup.matched_id}). O'tkazib yuborildi."
            )
            QueueManager().update_status(
                item.id,
                "already_exists",
                error_message=f"Bazada mavjud: {sec_dup.reason} (ID: {sec_dup.matched_id})"
            )
            return False

        # ── Sifat nazorati (Quality Guard) ──
        # Agar sarlavha "Kino", "Film" kabi noaniq bo'lsa, bazaga va kanalga xato kirmasligi uchun to'xtatiladi
        GENERIC_WORDS = {"kino", "film", "serial", "tarjima kino", "premyera", "yangi kino", "noma'lum", "movie"}
        if (title.strip().lower() in GENERIC_WORDS or len(title.strip()) < 3) and item.status != "manually_verified":
            logger.warning(
                f"⚠️ [MODERATSIYA]: '{title}' nomi yetarli emas. Baza va kanal buzilmasligi uchun 'needs_review' holatiga o'tkazildi."
            )
            QueueManager().update_status(
                item.id,
                "needs_review",
                error_message=f"⚠️ Nomi noaniq ('{title}'). Moderatsiya bo'limida to'g'ri nomini kiriting."
            )
            return False

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
            poster_to_send = meta.get("poster_url")
            if not poster_to_send and card_msg and getattr(card_msg, "photo", None):
                poster_to_send = card_msg.photo

            if poster_to_send:
                try:
                    await self.client.send_file(
                        target_chat,
                        file=poster_to_send,
                        caption=welcome_text,
                        reply_to=thread_id,
                        parse_mode="html"
                    )
                except Exception as pe:
                    logger.warning(f"Poster yuborishda xatolik: {pe}, matn yuborilmoqda...")
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
                source_chat_id=int(target_chat) if (isinstance(target_chat, int) or (isinstance(target_chat, str) and target_chat.lstrip('-').isdigit())) else 0,
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
            # Bo'sh qolgan filmni bazadan xavfsiz tozalash
            try:
                from sqlalchemy import text
                async with async_session_factory() as cleanup_session:
                    await cleanup_session.execute(text("DELETE FROM movie_category WHERE movie_id = :mid"), {"mid": movie_id})
                    await cleanup_session.execute(text("DELETE FROM page_movie WHERE movie_id = :mid"), {"mid": movie_id})
                    await cleanup_session.execute(text("DELETE FROM movies WHERE id = :mid"), {"mid": movie_id})
                    await cleanup_session.commit()
                logger.info(f"🧹 Chala qolgan film (ID: {movie_id}) bazadan muvaffaqiyatli tozalandi.")
            except Exception as cl_err:
                logger.warning(f"Chala filmni tozalashda xatolik: {cl_err}")
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
            logger.warning("Storage kanalga ko'chirishda xatolik yuz berdi, lekin video Topicda bor. Topic videosi bog'lanadi.")
            storage_msg = topic_video_msg

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
        actual_bot = target_bot
        if item and getattr(item, "source", None) == "asilmedia":
            actual_bot = "asilmediabot"
        elif item and getattr(item, "source", None) == "uzmovi":
            actual_bot = "UzmovieTV_Bot"
        is_uzmovie = "uzmovie" in actual_bot.lower()

        search_query = ""
        if code:
            search_query = str(code).strip()
        elif item:
            if item.source == "asilmedia" and not is_uzmovie:
                num_match = re.search(r'\d+', item.id)
                if num_match and len(num_match.group(0)) <= 6:
                    search_query = num_match.group(0)

            # Agar uzmovi bo'lsa yoki asilmedia kodi bo'lmasa, tozalangan film nomidan foydalanamiz
            if not search_query:
                clean_name = item.title.split('/')[0].split('|')[0].strip()
                clean_name = re.sub(r'\(.*?\)', '', clean_name).strip()
                clean_name = re.sub(r'^\d+\s+', '', clean_name).strip()
                clean_name = clean_movie_title(clean_name)
                search_query = clean_name

        if not search_query:
            logger.warning("Botga yuborish uchun so'rov topilmadi!")
            return None

        if not is_uzmovie:
            return await self._fetch_asilmedia_video(query=search_query, year=item.year if item else None)

        # UzmovieTV_Bot orqali video olish (avval raqamli kod yoki Telegram Inline Query orqali)
        uz_code = code if (code and str(code).strip().isdigit()) else None
        uz_video = await self._fetch_uzmovie_video(query=search_query, code=uz_code)
        if uz_video:
            return uz_video

        # Agar UzmovieTV_Bot da topilmasa, film nomi bo'yicha zaxira tarzida Asilmediada sinab ko'rish
        if item and item.title:
            clean_name = item.title.split('/')[0].split('|')[0].strip()
            clean_name = re.sub(r'\(.*?\)', '', clean_name).strip()
            clean_name = re.sub(r'^\d+\s+', '', clean_name).strip()
            clean_name = clean_movie_title(clean_name)
            if clean_name:
                logger.info(f"UzmovieTV_Bot dan olinmadi. Zaxira tarzida @asilmediabot dan '{clean_name}' qidirilmoqda...")
                return await self._fetch_asilmedia_video(query=clean_name, year=item.year)

        return None

    async def _fetch_uzmovie_video(
        self,
        query: str,
        code: Optional[str] = None
    ) -> Optional[Message]:
        bot = "UzmovieTV_Bot"

        # 1. Agar to'g'ridan-to'g'ri raqamli bot kodi mavjud bo'lsa
        if code and str(code).strip().isdigit():
            clean_code = str(code).strip()
            logger.info(f"[@{bot}] botiga kod yuborilmoqda: '{clean_code}'...")
            sent = await self.client.send_message(bot, clean_code)
            def has_uzmovie_reply(msgs):
                return any(m.file or "topilmadi" in (m.text or "").lower() for m in msgs)
            recent = await poll_new_messages(self.client, bot, sent.id, timeout=6.0, condition=has_uzmovie_reply)
            for m in recent:
                if m.file:
                    logger.info(f"✅ [@{bot}] dan video muvaffaqiyatli qabul qilindi (Kod #{clean_code})!")
                    return m

        # 2. Film nomi bo'yicha Telegram INLINE QUERY orqali qidirish
        clean_name = query.split('/')[0].split('|')[0].strip()
        clean_name = re.sub(r'\(.*?\)', '', clean_name).strip()
        clean_name = re.sub(r'^\d+\s+', '', clean_name).strip()
        clean_name = clean_movie_title(clean_name)
        if not clean_name:
            return None

        logger.info(f"[@{bot}] Inline qidiruv orqali qidirilmoqda: '{clean_name}'...")
        try:
            results = await self.client.inline_query(bot, clean_name)
            if results:
                best_res = results[0]
                for res in results:
                    r_title = (getattr(res, 'title', '') or '').lower()
                    if clean_name.lower() in r_title or r_title in clean_name.lower():
                        best_res = res
                        break

                logger.info(f"[@{bot}] Inline natija tanlandi: '{best_res.title}'. Yuborilmoqda...")
                sent_inline = await best_res.click(bot)
                if sent_inline and sent_inline.file:
                    logger.info(f"✅ [@{bot}] dan inline video qabul qilindi! ({sent_inline.file.name or 'fayl'})")
                    return sent_inline
                click_id = sent_inline.id if sent_inline else 0

                def has_uzmovie_video(msgs):
                    return any(m.file for m in msgs)

                v_list = await poll_new_messages(
                    self.client,
                    bot,
                    click_id,
                    timeout=14.0,
                    interval=0.4,
                    condition=has_uzmovie_video
                )
                for vm in v_list:
                    if vm.file:
                        logger.info(f"✅ [@{bot}] dan inline video qabul qilindi! ({vm.file.name or 'fayl'})")
                        return vm
            else:
                logger.info(f"[@{bot}] Inline qidiruvda '{clean_name}' topilmadi.")
        except Exception as e:
            logger.warning(f"[@{bot}] Inline qidiruvda xatolik: {e}")

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
            for m in recent_msgs:
                if m.buttons:
                    has_series_btn = any(b for row in m.buttons for b in row if b.text.strip().isdigit() or "qism" in b.text.lower() or "fasl" in b.text.lower() or "mavsum" in b.text.lower())
                    if has_series_btn:
                        self._last_card_msg = m
                        logger.info(f"[@{bot}] Serial kartasi/tugmalari aniqlandi.")
                        return None
                    has_pending = any("tayyor bo'lganda" in b.text.lower() or "saqlash" in b.text.lower() for row in m.buttons for b in row) or ("yuklanmoqda" in (m.text or "").lower())
                    if has_pending:
                        self._last_unreleased_notice = "Film hali botga yuklanmagan (Tez kunda / 'Tayyor bo'lganda yuboring' holatida)"
                        logger.warning(f"[@{bot}] {self._last_unreleased_notice}")
                        return None
            logger.warning(f"[@{bot}] Film kartasi yoki sifat tugmalari topilmadi.")
            return None

        self._last_card_msg = card_msg

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
        await asyncio.sleep(2.0)
        _, q_flood = await self.safe_click(card_msg, r_idx, c_idx)
        if q_flood > 0:
            logger.warning(f"⏳ [@{bot}] Sifat bosishda flood cheklovi: {q_flood} soniya kutilmoqda...")
            await asyncio.sleep(q_flood)
            await self.safe_click(card_msg, r_idx, c_idx)

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
            return any(is_bot_flood_text(vm.text) or is_valid_vid(vm) for vm in msgs)

        video_replies = await poll_new_messages(self.client, bot, quality_click_id, timeout=20.0, interval=0.4, condition=has_asil_video)
        v_flood = get_flood_wait_seconds(video_replies)
        if v_flood > 0:
            logger.warning(f"⏳ [@{bot}] Video kutishda flood: {v_flood}s kutilmoqda...")
            await asyncio.sleep(v_flood)
            await self.safe_click(card_msg, r_idx, c_idx)
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
                    await asyncio.sleep(2.0)
                    await self.safe_click(card_msg, f_r, f_c)
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
            # 0. 2000 MB (2 GB) chegarasi (Telegram non-premium akkauntlarining qat'iy limiti)
            if hasattr(video_msg, "file") and video_msg.file and getattr(video_msg.file, "size", 0) > 2000 * 1024 * 1024:
                file_mb = round(video_msg.file.size / 1024 / 1024, 1)
                logger.warning(f"⚠️ Fayl hajmi juda katta ({file_mb} MB > 2000 MB). Telegram non-premium limiti tufayli o'tkazib yuborildi.")
                print(f"⚠️ Fayl hajmi juda katta ({file_mb} MB > 2000 MB). Telegram limiti tufayli o'tkazib yuborildi.", flush=True)
                return None

            peer = await self.client.get_input_entity(target_chat)
            # Server-side copy (juda tez va tejamkor - 1 soniya):
            try:
                media_to_send = getattr(video_msg.media, "document", video_msg.media) if hasattr(video_msg, "media") and video_msg.media else video_msg
                try:
                    sent_msg = await self.client.send_file(
                        peer,
                        file=media_to_send,
                        caption=caption,
                        reply_to=reply_to,
                        supports_streaming=True,
                        parse_mode="html"
                    )
                except Exception:
                    clean_cap = re.sub(r'<[^>]+>', '', caption) if caption else None
                    sent_msg = await self.client.send_file(
                        peer,
                        file=media_to_send,
                        caption=clean_cap,
                        reply_to=reply_to,
                        supports_streaming=True
                    )
                if sent_msg:
                    logger.info("⚡ Server-side nusxalash muvaffaqiyatli bajarildi!")
                    print("⚡ Server-side tezkor nusxalandi!", flush=True)
                    return sent_msg
            except Exception as copy_err:
                logger.info(f"Server-side nusxalab bo'lmadi ({copy_err}), yuklab yuklash usuli bajarilmoqda...")

            # Yuklab yuklash (himoyalangan botlar uchun MTProto yo'li)
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
                    print(f"  📥 Yuklab olish: {pct}% ({mb_cur}MB / {mb_tot}MB)", flush=True)
                    last_logged[0] = now

            logger.info("⚡ Parallel tezkor yuklab olish boshlandi...")
            print("⚡ Katta faylni tezkor yuklab olish boshlandi...", flush=True)
            raw_filename = video_msg.file.name if (video_msg.file and video_msg.file.name) else f"video_{video_msg.id}.mp4"
            target_file_path = os.path.join(downloads_dir, raw_filename)

            try:
                file_path = await fast_download(
                    client=self.client,
                    location_or_msg=video_msg,
                    out_file_path=target_file_path,
                    progress_callback=dl_progress,
                    connection_count=6,
                    part_size_kb=512
                )
            except Exception as dl_err:
                logger.warning(f"Fast download da xatolik ({dl_err}), standart usulga o'tilmoqda...")
                try:
                    file_path = await self.client.download_media(video_msg, file=downloads_dir, progress_callback=dl_progress)
                except Exception as std_err:
                    logger.error(f"Standart download da ham xatolik: {std_err}")
                    file_path = None

            if not file_path or not os.path.exists(file_path):
                logger.error("Videoni yuklab olib bo'lmadi!")
                return None

            total_mb = round(os.path.getsize(file_path) / 1024 / 1024, 1)
            logger.info(f"⚡ Parallel chatga yuklash boshlandi ({total_mb} MB)...")
            print(f"⚡ Telegramga yuklash boshlandi ({total_mb} MB)...", flush=True)

            last_ul = [0.0]
            def ul_progress(current, total):
                now = time.time()
                if now - last_ul[0] >= 3.0 or current == total:
                    pct = round(current / total * 100, 1) if total else 0
                    mb_cur = round(current / 1024 / 1024, 1)
                    mb_tot = round(total / 1024 / 1024, 1)
                    logger.info(f"  📤 Yuklash: {pct}% ({mb_cur}MB / {mb_tot}MB)")
                    print(f"  📤 Telegramga yuklash: {pct}% ({mb_cur}MB / {mb_tot}MB)", flush=True)
                    last_ul[0] = now

            peer = await self.client.get_input_entity(target_chat)
            sent_msg = None
            try:
                uploaded_input_file = await fast_upload(
                    client=self.client,
                    file_path=file_path,
                    progress_callback=ul_progress,
                    connection_count=6,
                    part_size_kb=512
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
    parser.add_argument("--max-episodes", type=int, default=None, help="Maksimal yuklanadigan qismlar soni")
    args = parser.parse_args()

    bot_username = TARGET_BOTS.get(args.target, args.target)
    checker = DuplicateChecker()
    await checker.refresh_cache(force=True)

    client = create_telethon_client()
    await client.connect()
    pipeline = TelethonModeratorPipeline(client=client, duplicate_checker=checker)
    try:
        if args.code:
            await pipeline.run_by_code(code=args.code, target_bot=bot_username, max_episodes=args.max_episodes)
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

