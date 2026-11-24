import pytest
import logging
from unittest.mock import AsyncMock, MagicMock, patch
from aiogram.types import Message, User, Chat
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from middlewares.subscription_check import SubscriptionMiddleware

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


@pytest.mark.asyncio
async def test_subscription_normalizes_tme_url_and_blocks():
    """https://t.me/yangi_kanal ko'rinishidagi yozuv @yangi_kanal ga normallashib tekshirilishi kerak."""
    middleware = SubscriptionMiddleware()
    handler = AsyncMock()

    user = User(id=22222, is_bot=False, first_name="Valijon")
    chat = Chat(id=22222, type="private")
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
        {"id": 404, "channel_id": None, "channel_username": "https://t.me/yangi_kanal/", "channel_title": "Yangi Kanal"}
    ]

    with patch("middlewares.subscription_check._get_channels_cached", new_callable=AsyncMock) as mock_channels:
        mock_channels.return_value = test_channels
        await middleware(handler, message, data)

        handler.assert_not_called()
        mock_bot.get_chat_member.assert_awaited_once_with(chat_id="@yangi_kanal", user_id=22222)
        message.answer.assert_called_once()
        markup = message.answer.call_args.kwargs.get("reply_markup")
        assert markup.inline_keyboard[0][0].url == "https://t.me/yangi_kanal"


@pytest.mark.asyncio
async def test_subscription_private_channel_id_blocks_and_rechecks_on_callback():
    """Yopiq kanal (+invite va channel_id) keshni chetlab check_subscription tugmasida ham bloklaydi."""
    from aiogram.types import CallbackQuery
    from middlewares.subscription_check import _user_sub_verified_cache

    middleware = SubscriptionMiddleware()
    handler = AsyncMock()

    user = User(id=33333, is_bot=False, first_name="Hasan")
    cb = MagicMock(spec=CallbackQuery)
    cb.from_user = user
    cb.data = "check_subscription"
    cb.answer = AsyncMock()

    _user_sub_verified_cache[33333] = 10**12  # oldin keshlangan bo'lsa ham check_subscription qayta tekshiradi

    mock_bot = MagicMock()
    mock_member = MagicMock()
    mock_member.status = "left"
    mock_bot.get_chat_member = AsyncMock(return_value=mock_member)

    test_channels = [
        {"id": 505, "channel_id": -1001234567890, "channel_username": "https://t.me/+SecretInvite", "channel_title": "Yopiq Kanal"}
    ]

    try:
        with patch("middlewares.subscription_check._get_channels_cached", new_callable=AsyncMock) as mock_channels:
            mock_channels.return_value = test_channels
            await middleware(handler, cb, {"bot": mock_bot})

            handler.assert_not_called()
            mock_bot.get_chat_member.assert_awaited_once_with(chat_id=-1001234567890, user_id=33333)
            cb.answer.assert_awaited_once()
    finally:
        _user_sub_verified_cache.pop(33333, None)


@pytest.mark.asyncio
async def test_subscription_fail_open_does_not_cache_and_start_bypasses_cache():
    """Fail-open natija keshlanmaydi va /start har doim jonli tekshiradi."""
    from middlewares.subscription_check import _user_sub_verified_cache

    middleware = SubscriptionMiddleware()
    handler = AsyncMock(return_value="ok")

    user = User(id=44444, is_bot=False, first_name="Olim")
    chat = Chat(id=44444, type="private")
    msg_fail_open = MagicMock(spec=Message)
    msg_fail_open.from_user = user
    msg_fail_open.chat = chat
    msg_fail_open.text = "kino"
    msg_fail_open.answer = AsyncMock()

    mock_bot = MagicMock()
    mock_bot.get_chat_member = AsyncMock(
        side_effect=TelegramBadRequest(method=MagicMock(), message="Chat not found")
    )

    test_channels = [
        {"id": 606, "channel_id": -1009998887776, "channel_username": "MediaPlusOfficial", "channel_title": "Kanal"}
    ]

    try:
        _user_sub_verified_cache.pop(44444, None)
        with patch("middlewares.subscription_check._get_channels_cached", new_callable=AsyncMock) as mock_channels:
            mock_channels.return_value = test_channels
            await middleware(handler, msg_fail_open, {"bot": mock_bot})
            assert 44444 not in _user_sub_verified_cache

        # Keshlangan bo'lsa ham /start jonli tekshirib obunasiz userni bloklashi shart
        _user_sub_verified_cache[44444] = 10**12
        msg_start = MagicMock(spec=Message)
        msg_start.from_user = user
        msg_start.chat = chat
        msg_start.text = "/start"
        msg_start.answer = AsyncMock()

        mock_member = MagicMock()
        mock_member.status = "left"
        mock_bot.get_chat_member = AsyncMock(return_value=mock_member)
        handler.reset_mock()

        with patch("middlewares.subscription_check._get_channels_cached", new_callable=AsyncMock) as mock_channels:
            mock_channels.return_value = test_channels
            await middleware(handler, msg_start, {"bot": mock_bot})
            handler.assert_not_called()
            msg_start.answer.assert_awaited_once()
    finally:
        _user_sub_verified_cache.pop(44444, None)
