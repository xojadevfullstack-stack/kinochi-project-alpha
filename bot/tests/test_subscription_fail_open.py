import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, CallbackQuery, User, Chat
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from middlewares.subscription_check import SubscriptionMiddleware, _get_channels_cached

@pytest.mark.asyncio
async def test_subscription_fail_open_on_bad_request(caplog):
    """TelegramBadRequest yuz berganda ogohlantirish log qilinadi va foydalanuvchi bloklanmaydi (fail-open)."""
    middleware = SubscriptionMiddleware()
    handler = AsyncMock(return_value="handler_result")
    
    user = User(id=12345, is_bot=False, first_name="Ali")
    chat = Chat(id=12345, type="private")
    message = MagicMock(spec=Message)
    message.from_user = user
    message.chat = chat
    message.answer = AsyncMock()

    mock_bot = MagicMock()
    # bot.get_chat_member TelegramBadRequest ko'targan holat
    mock_method = MagicMock()
    mock_bot.get_chat_member = AsyncMock(side_effect=TelegramBadRequest(method=mock_method, message="Chat not found"))

    data = {"bot": mock_bot}
    test_channels = [
        {"id": 101, "channel_id": "-1001234567890", "channel_username": "test_channel", "channel_title": "Test Kanal"}
    ]

    with patch("middlewares.subscription_check._get_channels_cached", new_callable=AsyncMock) as mock_channels:
        mock_channels.return_value = test_channels

        with caplog.at_level(logging.WARNING):
            result = await middleware(handler, message, data)

        # Handler chaqirilgan bo'lishi kerak (bloklanmagan)
        assert result == "handler_result"
        handler.assert_awaited_once_with(message, data)
        # message.answer (obuna bo'ling xabari) chaqirilmagan bo'lishi kerak
        message.answer.assert_not_called()
        # Logda kanal ID va fail-open haqida ogohlantirish mavjud bo'lishi kerak
        assert "-1001234567890" in caplog.text
        assert "Fail-open" in caplog.text


@pytest.mark.asyncio
async def test_subscription_fail_open_on_forbidden_error(caplog):
    """TelegramForbiddenError yuz berganda ogohlantirish log qilinadi va foydalanuvchi bloklanmaydi (fail-open)."""
    middleware = SubscriptionMiddleware()
    handler = AsyncMock(return_value="success_action")
    
    user = User(id=98765, is_bot=False, first_name="Vali")
    chat = Chat(id=98765, type="private")
    message = MagicMock(spec=Message)
    message.from_user = user
    message.chat = chat
    message.answer = AsyncMock()

    mock_bot = MagicMock()
    # bot.get_chat_member TelegramForbiddenError ko'targan holat (bot kanaldan haydalgan yoki huquqi yo'q)
    mock_method = MagicMock()
    mock_bot.get_chat_member = AsyncMock(side_effect=TelegramForbiddenError(method=mock_method, message="Forbidden: bot was kicked"))

    data = {"bot": mock_bot}
    test_channels = [
        {"id": 202, "channel_id": "-1009876543210", "channel_username": "forbidden_channel", "channel_title": "Maxfiy Kanal"}
    ]

    with patch("middlewares.subscription_check._get_channels_cached", new_callable=AsyncMock) as mock_channels:
        mock_channels.return_value = test_channels

        with caplog.at_level(logging.WARNING):
            result = await middleware(handler, message, data)

        # Handler chaqirilgan bo'lishi kerak (foydalanuvchi bloklanmaydi)
        assert result == "success_action"
        handler.assert_awaited_once_with(message, data)
        message.answer.assert_not_called()
        assert "-1009876543210" in caplog.text
        assert "Fail-open" in caplog.text


@pytest.mark.asyncio
async def test_subscription_blocks_when_actually_unsubscribed():
    """Haqiqatdan a'zo bo'lmagan foydalanuvchi bloklanadi va kanal ro'yxati ko'rsatiladi."""
    middleware = SubscriptionMiddleware()
    handler = AsyncMock()
    
    user = User(id=11111, is_bot=False, first_name="Hasan")
    chat = Chat(id=11111, type="private")
    message = MagicMock(spec=Message)
    message.from_user = user
    message.chat = chat
    message.answer = AsyncMock()

    mock_bot = MagicMock()
    mock_member = MagicMock()
    mock_member.status = "left"
    mock_bot.get_chat_member = AsyncMock(return_value=mock_member)

    data = {"bot": mock_bot}
    test_channels = [
        {"id": 303, "channel_id": "-1001112223334", "channel_username": "public_chan", "channel_title": "Ochiq Kanal"}
    ]

    with patch("middlewares.subscription_check._get_channels_cached", new_callable=AsyncMock) as mock_channels:
        mock_channels.return_value = test_channels

        await middleware(handler, message, data)

        # Foydalanuvchi obuna bo'lmagani sababli handler chaqirilmasligi kerak
        handler.assert_not_called()
        # Obuna bo'lish so'ralgan xabar yuborilgan
        message.answer.assert_called_once()
        assert "obuna bo'ling" in message.answer.call_args[0][0]
