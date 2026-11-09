import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineQuery
from services.api_client import api_client

logger = logging.getLogger(__name__)


class BanCheckMiddleware(BaseMiddleware):
    """
    Middleware to check if the user is banned in the system.
    If banned, prevents execution of any handler and sends an informative alert.
    """
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        user = getattr(event, "from_user", None)
        if not user or not user.id:
            return await handler(event, data)

        try:
            is_banned = await api_client.check_user_banned(user.id)
            if is_banned:
                ban_text = (
                    "⛔️ <b>Sizning hisobingiz ma'muriyat tomonidan bloklangan.</b>\n\n"
                    "Agar bu xatolik deb hisoblasangiz, ma'muriyatga murojaat qiling."
                )
                if isinstance(event, CallbackQuery):
                    try:
                        await event.answer(
                            "⛔️ Sizning hisobingiz ma'muriyat tomonidan bloklangan.",
                            show_alert=True
                        )
                    except Exception:
                        pass
                elif isinstance(event, Message):
                    try:
                        await event.answer(ban_text, parse_mode="HTML")
                    except Exception:
                        pass
                elif isinstance(event, InlineQuery):
                    try:
                        await event.answer(
                            results=[],
                            switch_pm_text="⛔️ Hisobingiz bloklangan",
                            switch_pm_parameter="banned",
                            is_personal=True,
                            cache_time=10,
                        )
                    except Exception:
                        pass
                return None
        except Exception as e:
            logger.warning(f"Error checking ban status for user {user.id}: {e}")

        return await handler(event, data)
