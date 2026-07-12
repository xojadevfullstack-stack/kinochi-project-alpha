from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from services.api_client import api_client
import time
import logging

logger = logging.getLogger(__name__)

# ── In-memory channel cache (60 soniyalik TTL) ───────────────────────────
_channels_cache: list = []
_channels_cache_time: float = 0.0
_CACHE_TTL = 60  # seconds

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

        user_id = event.from_user.id
        bot = data['bot']

        channels = await _get_channels_cached()
        if not channels:
            return await handler(event, data)

        unsubscribed_channels = []
        for ch in channels:
            chat_identifier = ch.get('channel_username')
            if chat_identifier:
                if not chat_identifier.startswith('@'):
                    chat_identifier = f"@{chat_identifier}"
            else:
                # channel_id None bo'lsa, skip — KeyError yoki None argument oldini olamiz
                chat_identifier = ch.get('channel_id')
                if not chat_identifier:
                    logger.warning(f"Kanal identifikatorsiz topildi, o'tkazib yuborildi: {ch}")
                    continue

            try:
                member = await bot.get_chat_member(chat_id=chat_identifier, user_id=user_id)
                if member.status in ["left", "kicked"]:
                    unsubscribed_channels.append(ch)
            except TelegramBadRequest as e:
                # Bot admin emas yoki chat topilmadi => obuna tekshirib bo'lmaydi
                logging.warning(f"Obuna tekshiruvi muvaffaqiyatsiz: {chat_identifier} — {e}")
                unsubscribed_channels.append(ch)

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

        return await handler(event, data)

