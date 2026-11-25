"""Lightweight isolated legacy bot runner that redirects users to the new bot/channel."""
from __future__ import annotations

import asyncio
import logging
import os
import re
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandObject, CommandStart
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

try:
    from config import settings
except ImportError:  # pragma: no cover
    from bot.config import settings

logger = logging.getLogger(__name__)


def _normalize_username(raw_username: str) -> str:
    return (raw_username or "kinochi_mvp_bot").strip().lstrip("@")


def build_redirect_target_url(target_bot_username: str, start_payload: Optional[str] = None) -> str:
    """Build https://t.me/<new_bot>?start=<payload> preserving valid deep-link codes."""
    clean_bot = _normalize_username(target_bot_username)
    clean_payload = re.sub(r"[^A-Za-z0-9_-]", "", (start_payload or "").strip())[:64]
    if clean_payload:
        return f"https://t.me/{clean_bot}?start={clean_payload}"
    return f"https://t.me/{clean_bot}"


def build_redirect_reply(
    target_bot_username: str,
    start_payload: Optional[str] = None,
    channel_url: Optional[str] = None,
) -> tuple[str, InlineKeyboardMarkup]:
    """Build Uzbek redirect message and inline button(s) pointing to the new bot and optional channel."""
    clean_bot = _normalize_username(target_bot_username)
    bot_url = build_redirect_target_url(clean_bot, start_payload=start_payload)
    rows = [[InlineKeyboardButton(text="🚀 Yangi botga o'tish", url=bot_url)]]
    clean_channel = (channel_url or "").strip()
    if clean_channel:
        rows.append([InlineKeyboardButton(text="📢 Yangi Telegram kanalimiz", url=clean_channel)])
    text = (
        "🔄 <b>Botimiz yangi manzilga ko'chdi!</b>\n\n"
        f"Barcha kinolar, seriallar va kodlar endi yangi botda ishlaydi: @{clean_bot}\n"
        "Davom etish uchun quyidagi tugmani bosing 👇"
    )
    return text, InlineKeyboardMarkup(inline_keyboard=rows)


def _is_private_message(message: Optional[Message]) -> bool:
    chat_type = getattr(getattr(message, "chat", None), "type", None)
    return not (isinstance(chat_type, str) and chat_type != "private")


async def handle_legacy_start(
    message: Message,
    command: CommandObject,
    target_bot_username: str,
    channel_url: str = "",
) -> None:
    if not _is_private_message(message):
        return
    text, markup = build_redirect_reply(
        target_bot_username=target_bot_username,
        start_payload=getattr(command, "args", None),
        channel_url=channel_url,
    )
    await message.answer(text, parse_mode="HTML", reply_markup=markup)


async def handle_legacy_message(
    message: Message,
    target_bot_username: str,
    channel_url: str = "",
) -> None:
    if not _is_private_message(message):
        return
    raw_text = getattr(message, "text", None)
    raw = raw_text.strip() if isinstance(raw_text, str) else ""
    payload = raw if raw and re.fullmatch(r"[A-Za-z0-9_-]{1,32}", raw) else None
    text, markup = build_redirect_reply(
        target_bot_username=target_bot_username,
        start_payload=payload,
        channel_url=channel_url,
    )
    await message.answer(text, parse_mode="HTML", reply_markup=markup)


async def handle_legacy_callback(
    callback: CallbackQuery,
    target_bot_username: str,
    channel_url: str = "",
) -> None:
    if not callback.message or not _is_private_message(callback.message):
        return
    text, markup = build_redirect_reply(target_bot_username=target_bot_username, channel_url=channel_url)
    await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
    await callback.answer()


def create_redirect_dispatcher(target_bot_username: str, channel_url: str = "") -> Dispatcher:
    """Create minimal aiogram Dispatcher for the legacy redirect-only bot."""
    dp = Dispatcher()

    @dp.message(CommandStart(), F.chat.type == "private")
    async def _on_start(message: Message, command: CommandObject):
        await handle_legacy_start(message, command, target_bot_username, channel_url)

    @dp.message(F.chat.type == "private")
    async def _on_message(message: Message):
        await handle_legacy_message(message, target_bot_username, channel_url)

    @dp.callback_query(F.message.chat.type == "private")
    async def _on_callback(callback: CallbackQuery):
        await handle_legacy_callback(callback, target_bot_username, channel_url)

    return dp


async def supervised_run_redirect_bot() -> str:
    """Run legacy redirect bot alongside the main bot when LEGACY_BOT_TOKEN is configured."""
    token = (getattr(settings, "LEGACY_BOT_TOKEN", "") or os.getenv("LEGACY_BOT_TOKEN", "")).strip()
    main_token = (getattr(settings, "BOT_TOKEN", "") or os.getenv("BOT_TOKEN", "")).strip()
    if not token or token == main_token:
        logger.info("[REDIRECT_BOT] Disabled (LEGACY_BOT_TOKEN bo'sh yoki asosiy BOT_TOKEN bilan bir xil).")
        return "disabled"

    target_username = (getattr(settings, "BOT_USERNAME", "") or os.getenv("BOT_USERNAME", "kinochi_mvp_bot")).strip()
    channel_url = (getattr(settings, "REDIRECT_CHANNEL_URL", "") or os.getenv("REDIRECT_CHANNEL_URL", "")).strip()

    while True:
        bot = Bot(token=token)
        dp = create_redirect_dispatcher(target_bot_username=target_username, channel_url=channel_url)
        try:
            logger.info("[REDIRECT_BOT] Starting polling -> target @%s", _normalize_username(target_username))
            await dp.start_polling(bot, drop_pending_updates=False)
            return "stopped"
        except (KeyboardInterrupt, asyncio.CancelledError):
            raise
        except Exception as exc:
            logger.warning("[REDIRECT_BOT] Polling error (asosiy bot va API ta'sirlanmaydi): %s", exc)
            await asyncio.sleep(30)
        finally:
            try:
                await bot.session.close()
            except Exception:
                pass
