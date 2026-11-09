import pytest
from unittest.mock import AsyncMock, MagicMock
from services.api_client import APIClient
from handlers.reports import handle_execute_report
from aiogram.types import CallbackQuery, User, Message


@pytest.mark.asyncio
async def test_api_client_submit_report_includes_telegram_user_id():
    """APIClient.submit_report sends telegram_user_id in post data."""
    client = APIClient()
    client.client = AsyncMock()
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    client.client.post.return_value = mock_resp

    success = await client.submit_report(
        media_type="movie",
        issue_type="video_xato",
        movie_id=10,
        description="Video ishlamayapti",
        telegram_user_id=123456789
    )

    assert success is True
    client.client.post.assert_called_once()
    call_args = client.client.post.call_args
    assert call_args[0][0] == "/reports"
    post_data = call_args[1].get("data")
    assert post_data["telegram_user_id"] == "123456789"
    assert post_data["media_type"] == "movie"
    assert post_data["issue_type"] == "video_xato"


@pytest.mark.asyncio
async def test_handle_execute_report_passes_user_id_to_submit_report(monkeypatch):
    """handle_execute_report passes callback.from_user.id to submit_report."""
    mock_api = AsyncMock()
    mock_api.get_movie_by_code.return_value = {"id": 101, "title": "Inception"}
    mock_api.submit_report.return_value = True
    monkeypatch.setattr("handlers.reports.api_client", mock_api)

    user = MagicMock(spec=User)
    user.id = 88888
    user.username = "rep_user"

    msg = MagicMock(spec=Message)
    msg.edit_text = AsyncMock()

    callback = MagicMock(spec=CallbackQuery)
    callback.from_user = user
    callback.data = "rep_do:m:K001:video_xato"
    callback.message = msg
    callback.answer = AsyncMock()

    await handle_execute_report(callback)

    mock_api.submit_report.assert_called_once()
    kwargs = mock_api.submit_report.call_args[1]
    assert kwargs.get("telegram_user_id") == 88888
    assert kwargs.get("media_type") == "movie"
    assert kwargs.get("issue_type") == "video_xato"
