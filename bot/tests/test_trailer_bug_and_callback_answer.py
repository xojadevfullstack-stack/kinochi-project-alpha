import pytest
import inspect
import ast
import os
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram.types import CallbackQuery, Message, User, Chat

from handlers.trailer import handle_movie_trailer, handle_series_trailer

@pytest.mark.asyncio
async def test_handle_movie_trailer_missing_trailer_shows_alert():
    """Film treyleri mavjud bo'lmaganda callback.answer(..., show_alert=True) chaqirilishi kerak."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "trailer_m_1001"
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 12345
    callback.message = MagicMock(spec=Message)
    callback.answer = AsyncMock()
    callback.message.answer = AsyncMock()

    with patch("handlers.trailer.api_client.get_movie_by_code", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"id": 1, "code": "1001", "trailer_url": None}
        
        await handle_movie_trailer(callback)

        # Message.answer show_alert bilan chaqirilmasligi kerak (TypeError oldini olish)
        callback.message.answer.assert_not_called()
        # callback.answer show_alert=True bilan chaqirilgan bo'lishi kerak
        callback.answer.assert_any_await("⚠️ Treyler topilmadi.", show_alert=True)


@pytest.mark.asyncio
async def test_handle_series_trailer_missing_trailer_shows_alert():
    """Serial treyleri mavjud bo'lmaganda callback.answer(..., show_alert=True) chaqirilishi kerak."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "trailer_s_2002"
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 12345
    callback.message = MagicMock(spec=Message)
    callback.answer = AsyncMock()
    callback.message.answer = AsyncMock()

    with patch("handlers.trailer.api_client.get_series_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {"id": 2002, "trailer_url": ""}
        
        await handle_series_trailer(callback)

        callback.message.answer.assert_not_called()
        callback.answer.assert_any_await("⚠️ Treyler topilmadi.", show_alert=True)


@pytest.mark.asyncio
async def test_handle_series_trailer_invalid_id_shows_alert():
    """Noto'g'ri serial ID berilganda callback.answer("⚠️ Xatolik.", show_alert=True) chaqirilishi kerak."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "trailer_s_invalid_id"
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 12345
    callback.message = MagicMock(spec=Message)
    callback.answer = AsyncMock()
    callback.message.answer = AsyncMock()

    await handle_series_trailer(callback)

    callback.message.answer.assert_not_called()
    callback.answer.assert_any_await("⚠️ Xatolik.", show_alert=True)


@pytest.mark.asyncio
async def test_trailer_handler_calls_finally_callback_answer_on_error():
    """Ichki xatolik yuz berganda ham finally bloki orqali callback.answer chaqirilishi shart."""
    callback = MagicMock(spec=CallbackQuery)
    callback.data = "trailer_m_1001"
    callback.from_user = MagicMock(spec=User)
    callback.from_user.id = 12345
    callback.message = MagicMock(spec=Message)
    callback.answer = AsyncMock()

    with patch("handlers.trailer.api_client.get_movie_by_code", side_effect=RuntimeError("API error")):
        with pytest.raises(RuntimeError):
            await handle_movie_trailer(callback)

        # finally bloki orqali callback.answer chaqirilgan
        callback.answer.assert_called()


def test_every_callback_handler_has_finally_callback_answer():
    """bot/handlers dagi barcha callback handlerlar finally blokida callback.answer chaqirishi shart."""
    handlers_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "handlers"))
    
    tested_handlers = 0
    for filename in os.listdir(handlers_dir):
        if not filename.endswith(".py"):
            continue
        filepath = os.path.join(handlers_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()

        tree = ast.parse(code, filename=filename)

        for node in ast.walk(tree):
            if isinstance(node, ast.AsyncFunctionDef):
                # Check if decorated with router.callback_query
                is_callback_handler = False
                for dec in node.decorator_list:
                    dec_src = ast.unparse(dec)
                    if "callback_query" in dec_src:
                        is_callback_handler = True
                        break

                if is_callback_handler:
                    tested_handlers += 1
                    # Check that the function contains a Try node whose finalbody calls callback.answer
                    found_finally_answer = False
                    for child in node.body:
                        if isinstance(child, ast.Try) and child.finalbody:
                            finally_src = ast.unparse(child.finalbody)
                            if "callback.answer()" in finally_src:
                                found_finally_answer = True
                                break

                    assert found_finally_answer, (
                        f"Handler {node.name} in {filename} does not call callback.answer() in a finally block!"
                    )

    assert tested_handlers >= 25, f"Expected at least 25 callback handlers, found {tested_handlers}"
