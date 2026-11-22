import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from aiogram.filters import CommandObject

from handlers.start import cmd_start
from utils.info_sender import send_movie_info


@pytest.mark.asyncio
async def test_send_movie_info_displays_short_code_when_present():
    bot = AsyncMock()
    movie = {
        "id": 5,
        "title": "Interstellar",
        "code": "INT88X",
        "short_code": "1042",
        "release_year": 2014,
        "imdb_rating": 8.7,
        "description": "Kosmos haqida film",
    }
    with patch("utils.info_sender.api_client.get_movie_franchise_context", new=AsyncMock(return_value=None)):
        await send_movie_info(bot, chat_id=123, movie=movie)

    sent_kwargs = bot.send_message.await_args.kwargs
    assert "<code>1042</code>" in sent_kwargs["text"]
    # Callback data keeps legacy code for compatibility
    markup = sent_kwargs["reply_markup"]
    btn_callbacks = [b.callback_data for row in markup.inline_keyboard for b in row if b.callback_data]
    assert "watch_m_INT88X" in btn_callbacks


@pytest.mark.asyncio
async def test_cmd_start_missing_code_provides_search_and_catalog_buttons():
    message = AsyncMock()
    message.from_user = SimpleNamespace(id=111, username="xoja", first_name="Xoja", last_name=None)
    message.bot = AsyncMock()
    command = CommandObject(prefix="/", command="start", args="999999")

    with (
        patch("handlers.start.api_client.register_user", new=AsyncMock(return_value={"is_banned": False})),
        patch("utils.code_resolver.resolve_and_send_content", new=AsyncMock(return_value=False)),
    ):
        await cmd_start(message, command)

    kwargs = message.answer.await_args.kwargs
    assert "reply_markup" in kwargs and kwargs["reply_markup"] is not None
    buttons = [b for row in kwargs["reply_markup"].inline_keyboard for b in row]
    assert any(b.switch_inline_query_current_chat == "" for b in buttons)
    assert any(b.callback_data == "menu_catalog" for b in buttons)
