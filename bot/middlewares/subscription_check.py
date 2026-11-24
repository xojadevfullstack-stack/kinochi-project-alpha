from typing import Any, Awaitable, Callable, Dict
import logging
import re
import time
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from services.api_client import api_client

logger = logging.getLogger(__name__)

# ── In-memory channel cache (20 soniyalik TTL — Admin o'zgarishlari tez aks etishi uchun) ──
_channels_cache: list = []
_channels_cache_time: float = 0.0
_channels_signature: tuple = ()
_CACHE_TTL = 20  # seconds

# ── In-memory user subscription verified cache (60 soniyalik TTL) ────────
_user_sub_verified_cache: dict[int, float] = {}
_VERIFIED_CACHE_TTL = 60.0

def invalidate_user_sub_cache(user_id: int):
    """Foydalanuvchi tekshirish tugmasini bosganda keshni yangilash uchun."""
    _user_sub_verified_cache.pop(user_id, None)


def _normalize_username(raw: Any) -> str:
    """Normalizes channel username / t.me link into clean bare handle (without @ or URL)."""
    if not raw:
        return ""
    val = str(raw).strip()
    val = re.sub(r"^https?://(?:www\.)?(?:t\.me|telegram\.me)/", "", val, flags=re.IGNORECASE)
    val = val.strip().strip("/").lstrip("@").strip()
    return val


def _extract_chat_targets(ch: dict) -> list[Any]:
    """Returns ordered chat_id candidates for bot.get_chat_member."""
    targets: list[Any] = []
    raw_user = str(ch.get("channel_username") or "").strip()
    clean_user = _normalize_username(raw_user)
    if clean_user and not clean_user.startswith("+") and not clean_user.lower().startswith("joinchat"):
        if re.fullmatch(r"[A-Za-z0-9_]{3,}", clean_user):
            targets.append(f"@{clean_user}")
    raw_id = ch.get("channel_id")
    if raw_id is not None and str(raw_id).strip():
        candidate = int(raw_id) if str(raw_id).lstrip("-").isdigit() else raw_id
        if candidate not in targets:
            targets.append(candidate)
    return targets


def _build_channel_button_url(ch: dict) -> str | None:
    raw_user = str(ch.get("channel_username") or "").strip()
    if raw_user.startswith("http://") or raw_user.startswith("https://"):
        return raw_user.rstrip("/")
    clean_user = _normalize_username(raw_user)
    if clean_user:
        return f"https://t.me/{clean_user}"
    return None


def _compute_channels_signature(channels: list) -> tuple:
    return tuple(
        (c.get("id"), c.get("channel_id"), c.get("channel_username"), c.get("is_active"))
        for c in (channels or [])
    )


async def _get_channels_cached() -> list:
    """Kanallar ro'yxatini 20 soniyalik TTL bilan keshdan qaytaradi; ro'yxat o'zgarsa user keshini tozalaydi."""
    global _channels_cache, _channels_cache_time, _channels_signature
    if time.monotonic() - _channels_cache_time > _CACHE_TTL:
        fresh = await api_client.get_active_channels()
        fresh_sig = _compute_channels_signature(fresh)
        if fresh_sig != _channels_signature:
            _user_sub_verified_cache.clear()
            _channels_signature = fresh_sig
        _channels_cache = fresh
        _channels_cache_time = time.monotonic()
    return _channels_cache


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id if event.from_user else None
        if not user_id:
            return await handler(event, data)

        channels = await _get_channels_cached()
        if not channels:
            return await handler(event, data)

        now = time.monotonic()
        raw_text = getattr(event, "text", None) if isinstance(event, Message) else None
        is_start_cmd = isinstance(raw_text, str) and raw_text.lstrip().startswith("/start")
        is_check_sub = isinstance(event, CallbackQuery) and event.data == "check_subscription"
        # /start va Tekshirish tugmasi har doim Telegram'dan jonli tekshiradi
        if not is_start_cmd and not is_check_sub and user_id in _user_sub_verified_cache and now < _user_sub_verified_cache[user_id]:
            return await handler(event, data)

        bot = data['bot']
        unsubscribed_channels = []
        all_checked = True
        for ch in channels:
            targets = _extract_chat_targets(ch)
            if not targets:
                all_checked = False
                logger.warning(f"Kanal identifikatorsiz topildi, o'tkazib yuborildi: {ch}")
                continue

            channel_id_ref = ch.get('channel_id') or ch.get('id') or targets[0]
            checked = False
            for chat_identifier in targets:
                if isinstance(chat_identifier, str) and chat_identifier.lower().endswith("bot"):
                    logger.warning(f"Kanal o'rniga bot username kiritilgan ({chat_identifier}); obuna tekshiruvi ishlamaydi.")
                try:
                    member = await bot.get_chat_member(chat_id=chat_identifier, user_id=user_id)
                    checked = True
                    status_val = getattr(member, "status", "")
                    if status_val in ("left", "kicked") or (
                        status_val == "restricted" and not getattr(member, "is_member", True)
                    ):
                        unsubscribed_channels.append(ch)
                    break
                except (TelegramBadRequest, TelegramForbiddenError) as e:
                    # Fail-open: Bot admin emas yoki chat topilmadi => keyingi targetni sinaymiz, aks holda bloklanmaydi
                    logger.warning(f"Obuna tekshiruvi muvaffaqiyatsiz (channel_id={channel_id_ref}, chat={chat_identifier}): {e}. Fail-open: foydalanuvchi bloklanmadi.")
            if not checked:
                all_checked = False
                continue

        if unsubscribed_channels:
            _user_sub_verified_cache.pop(user_id, None)
            buttons = []
            for ch in unsubscribed_channels:
                url = _build_channel_button_url(ch)
                if url:
                    btn_text = ch.get('channel_title') or "Kanal"
                    buttons.append([InlineKeyboardButton(text=btn_text, url=url)])

            buttons.append([InlineKeyboardButton(text="✅ Tekshirish", callback_data="check_subscription")])
            keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

            text = "Botdan foydalanish uchun quyidagi kanal(lar)ga obuna bo'ling:"

            if isinstance(event, Message):
                await event.answer(text, reply_markup=keyboard)
            elif isinstance(event, CallbackQuery):
                if event.data == "check_subscription":
                    await event.answer("Hali hamma kanallarga obuna bo'lmadingiz!", show_alert=True)
                else:
                    await event.message.answer(text, reply_markup=keyboard)
                    await event.answer()
            return

        # Faqat barcha kanallar muvaffaqiyatli tekshirilganda qisqa keshda saqlaymiz (fail-open keshlanmaydi!)
        if all_checked:
            _user_sub_verified_cache[user_id] = now + _VERIFIED_CACHE_TTL
        return await handler(event, data)
