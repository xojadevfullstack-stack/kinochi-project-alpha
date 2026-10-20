from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from services.api_client import api_client
import time
import logging

logger = logging.getLogger(__name__)

# ── In-memory channel cache (60 soniyalik TTL) ───────────────────────────
_channels_cache: list = []
_channels_cache_time: float = 0.0
_CACHE_TTL = 60  # seconds

# ── In-memory user subscription verified cache (300 soniyalik TTL) ────────
_user_sub_verified_cache: dict[int, float] = {}

def invalidate_user_sub_cache(user_id: int):
    """Foydalanuvchi tekshirish tugmasini bosganda keshni yangilash uchun."""
    _user_sub_verified_cache.pop(user_id, None)

async def _get_channels_cached() -> list:
    """Kanallar ro'yxatini 60 soniyalik TTL bilan keshdan qaytaradi."""
    global _channels_cache, _channels_cache_time
    if time.monotonic() - _channels_cache_time > _CACHE_TTL:
        _channels_cache = await api_client.get_active_channels()
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
        # Agar foydalanuvchi oxirgi 5 daqiqada tekshirilgan bo'lsa, qayta Telegram API chaqirmaymiz
        if user_id in _user_sub_verified_cache and now < _user_sub_verified_cache[user_id]:
            return await handler(event, data)

        bot = data['bot']
        unsubscribed_channels = []
        for ch in channels:
            chat_identifier = ch.get('channel_username')
            if chat_identifier:
                if not chat_identifier.startswith('@'):
                    chat_identifier = f"@{chat_identifier}"
            else:
                chat_identifier = ch.get('channel_id')
                if not chat_identifier:
                    logger.warning(f"Kanal identifikatorsiz topildi, o'tkazib yuborildi: {ch}")
                    continue

            channel_id_ref = ch.get('channel_id') or ch.get('id') or chat_identifier
            try:
                member = await bot.get_chat_member(chat_id=chat_identifier, user_id=user_id)
                if member.status in ["left", "kicked"]:
                    unsubscribed_channels.append(ch)
            except (TelegramBadRequest, TelegramForbiddenError) as e:
                # Fail-open: Bot admin emas yoki chat topilmadi => kanal talab qilinganlar ro'yxatiga qo'shilmaydi va foydalanuvchi bloklanmaydi
                logger.warning(f"Obuna tekshiruvi muvaffaqiyatsiz (channel_id={channel_id_ref}, chat={chat_identifier}): {e}. Fail-open: foydalanuvchi bloklanmadi.")

        if unsubscribed_channels:
            buttons = []
            for ch in unsubscribed_channels:
                username = ch.get('channel_username')
                if username:
                    url = f"https://t.me/{username.lstrip('@')}"
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

        # Obunasi tasdiqlangan bo'lsa, 5 daqiqa keshda saqlaymiz
        _user_sub_verified_cache[user_id] = now + 300.0
        return await handler(event, data)
