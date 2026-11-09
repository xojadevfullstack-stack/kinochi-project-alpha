import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from app.api.v1.users import delete_history_item, clear_my_history


@pytest.mark.asyncio
async def test_delete_history_item_success():
    """User deletes a single history item."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_session.execute.return_value = mock_result

    await delete_history_item(
        history_id=15,
        user={"user_id": 42},
        session=mock_session
    )

    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_delete_history_item_not_found():
    """When history item does not exist or belongs to another user, raises 404."""
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.rowcount = 0
    mock_session.execute.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        await delete_history_item(
            history_id=999,
            user={"user_id": 42},
            session=mock_session
        )

    assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_clear_my_history_success():
    """User clears all their watch history."""
    mock_session = AsyncMock()

    await clear_my_history(
        user={"user_id": 42},
        session=mock_session
    )

    mock_session.execute.assert_called_once()
    mock_session.commit.assert_called_once()
