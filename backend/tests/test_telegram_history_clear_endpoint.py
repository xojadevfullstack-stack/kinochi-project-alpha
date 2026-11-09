import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from app.api.v1.users import clear_user_history_by_telegram, get_user_summary_by_telegram


@pytest.mark.asyncio
async def test_clear_user_history_by_telegram_success():
    """Bot clears watch history for a user by their telegram_id."""
    mock_session = AsyncMock()
    mock_service = AsyncMock()
    mock_user = MagicMock()
    mock_user.id = 77
    mock_user.telegram_id = 998877
    mock_service.get_by_telegram_id.return_value = mock_user

    await clear_user_history_by_telegram(
        telegram_id=998877,
        session=mock_session,
        service=mock_service
    )

    mock_service.get_by_telegram_id.assert_called_once_with(998877)
    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_clear_user_history_by_telegram_user_not_found():
    """Raises 404 if user not found for telegram_id."""
    mock_session = AsyncMock()
    mock_service = AsyncMock()
    mock_service.get_by_telegram_id.return_value = None

    with pytest.raises(HTTPException) as exc_info:
        await clear_user_history_by_telegram(
            telegram_id=123456,
            session=mock_session,
            service=mock_service
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_get_user_summary_includes_is_banned():
    """User summary for telegram bot must include is_banned flag."""
    mock_session = AsyncMock()
    mock_service = AsyncMock()
    mock_user = MagicMock()
    mock_user.id = 55
    mock_user.telegram_id = 112233
    mock_user.username = "test_user"
    mock_user.first_name = "Ali"
    mock_user.last_name = None
    mock_user.is_banned = True
    mock_user.joined_at = None
    mock_service.get_by_telegram_id.return_value = mock_user

    # Mock execute results for history, achievements, subscriptions
    mock_res_wh = MagicMock()
    mock_res_wh.scalars.return_value.all.return_value = []
    mock_res_count = MagicMock()
    mock_res_count.scalar.return_value = 0
    mock_res_ach = MagicMock()
    mock_res_ach.scalars.return_value.all.return_value = []
    mock_res_sub = MagicMock()
    mock_res_sub.scalars.return_value.all.return_value = []
    mock_res_col = MagicMock()
    mock_res_col.scalars.return_value.all.return_value = []

    mock_session.execute.side_effect = [
        mock_res_wh,
        mock_res_count,
        mock_res_ach,
        mock_res_sub,
        mock_res_col
    ]

    summary = await get_user_summary_by_telegram(
        telegram_id=112233,
        session=mock_session,
        service=mock_service
    )

    assert "user" in summary
    assert summary["user"]["is_banned"] is True
