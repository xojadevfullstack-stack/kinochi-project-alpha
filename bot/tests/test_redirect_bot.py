import os
import sys
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

BOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BOT_DIR not in sys.path:
    sys.path.insert(0, BOT_DIR)


def test_build_redirect_target_url_preserves_deep_link_payload():
    from redirect_bot import build_redirect_target_url

    assert build_redirect_target_url("@YangiKinoBot", "3956") == "https://t.me/YangiKinoBot?start=3956"
    assert build_redirect_target_url("YangiKinoBot", "s_1088_1_2") == "https://t.me/YangiKinoBot?start=s_1088_1_2"
    assert build_redirect_target_url("@YangiKinoBot", "") == "https://t.me/YangiKinoBot"
    assert build_redirect_target_url("@YangiKinoBot", "bad spaces!@#") == "https://t.me/YangiKinoBot?start=badspaces"


def test_build_redirect_reply_includes_new_bot_and_optional_channel_buttons():
    from redirect_bot import build_redirect_reply

    text, markup = build_redirect_reply(
        target_bot_username="YangiKinoBot",
        start_payload="3956",
        channel_url="https://t.me/yangi_kanal",
    )
    assert "@YangiKinoBot" in text
    assert markup.inline_keyboard[0][0].url == "https://t.me/YangiKinoBot?start=3956"
    assert markup.inline_keyboard[1][0].url == "https://t.me/yangi_kanal"

    _, markup_no_channel = build_redirect_reply(target_bot_username="@YangiKinoBot", start_payload=None, channel_url="")
    assert len(markup_no_channel.inline_keyboard) == 1
    assert markup_no_channel.inline_keyboard[0][0].url == "https://t.me/YangiKinoBot"


@pytest.mark.asyncio
async def test_redirect_handlers_reply_with_new_bot_link_for_start_text_and_callback():
    from redirect_bot import handle_legacy_callback, handle_legacy_message, handle_legacy_start

    msg = MagicMock()
    msg.answer = AsyncMock()
    cmd = SimpleNamespace(args="WPZ79R")

    await handle_legacy_start(msg, cmd, target_bot_username="@YangiKinoBot", channel_url="https://t.me/yangi_kanal")
    msg.answer.assert_awaited_once()
    kb = msg.answer.await_args.kwargs["reply_markup"]
    assert kb.inline_keyboard[0][0].url == "https://t.me/YangiKinoBot?start=WPZ79R"

    msg2 = MagicMock()
    msg2.answer = AsyncMock()
    await handle_legacy_message(msg2, target_bot_username="@YangiKinoBot", channel_url="")
    msg2.answer.assert_awaited_once()
    assert msg2.answer.await_args.kwargs["reply_markup"].inline_keyboard[0][0].url == "https://t.me/YangiKinoBot"

    cb = MagicMock()
    cb.message = MagicMock()
    cb.message.answer = AsyncMock()
    cb.answer = AsyncMock()
    await handle_legacy_callback(cb, target_bot_username="@YangiKinoBot", channel_url="")
    cb.message.answer.assert_awaited_once()
    cb.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_redirect_handlers_ignore_groups_supergroups_and_channels():
    from redirect_bot import (
        create_redirect_dispatcher,
        handle_legacy_callback,
        handle_legacy_message,
        handle_legacy_start,
    )

    for chat_type in ("group", "supergroup", "channel"):
        grp_msg = MagicMock()
        grp_msg.chat = SimpleNamespace(type=chat_type, id=-100123456)
        grp_msg.text = "Hello"
        grp_msg.answer = AsyncMock()

        await handle_legacy_start(grp_msg, SimpleNamespace(args="3956"), target_bot_username="@YangiKinoBot")
        await handle_legacy_message(grp_msg, target_bot_username="@YangiKinoBot")
        grp_msg.answer.assert_not_awaited()

        cb = MagicMock()
        cb.message = grp_msg
        cb.answer = AsyncMock()
        await handle_legacy_callback(cb, target_bot_username="@YangiKinoBot")
        grp_msg.answer.assert_not_awaited()
        cb.answer.assert_not_awaited()

    dp = create_redirect_dispatcher(target_bot_username="@YangiKinoBot")
    msg_handlers = dp.message.handlers
    assert len(msg_handlers) == 2
    assert all(len(h.filters) >= 1 for h in msg_handlers)


@pytest.mark.asyncio
async def test_supervised_run_redirect_bot_noops_when_legacy_token_empty(monkeypatch):
    from config import settings
    from redirect_bot import supervised_run_redirect_bot

    monkeypatch.setattr(settings, "LEGACY_BOT_TOKEN", "")
    res = await supervised_run_redirect_bot()
    assert res == "disabled"
