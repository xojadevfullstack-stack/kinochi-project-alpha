import pytest
from unittest.mock import AsyncMock
from fastapi import HTTPException
from app.api.v1.broadcasts import update_broadcast, delete_broadcast, BroadcastUpdate


@pytest.mark.asyncio
async def test_update_draft_broadcast_success():
    """Admin updates draft broadcast."""
    mock_service = AsyncMock()
    mock_service.update_broadcast.return_value = {
        "id": 1,
        "message_text": "Yangilangan xabar",
        "status": "draft",
        "total_recipients": 100,
        "sent_count": 0,
        "failed_count": 0,
        "created_at": "2026-11-09T18:00:00",
    }

    payload = BroadcastUpdate(message_text="Yangilangan xabar")
    result = await update_broadcast(
        broadcast_id=1,
        data=payload,
        service=mock_service,
        admin={"id": 1, "role": "admin"},
    )

    assert result["message_text"] == "Yangilangan xabar"
    mock_service.update_broadcast.assert_called_once()


@pytest.mark.asyncio
async def test_update_broadcast_not_allowed_or_not_found():
    """When broadcast is not draft or not found, raises 400."""
    mock_service = AsyncMock()
    mock_service.update_broadcast.return_value = None

    payload = BroadcastUpdate(message_text="Test")
    with pytest.raises(HTTPException) as exc_info:
        await update_broadcast(
            broadcast_id=2,
            data=payload,
            service=mock_service,
            admin={"id": 1, "role": "admin"},
        )

    assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_delete_broadcast_success():
    """Admin deletes a broadcast."""
    mock_service = AsyncMock()
    mock_service.delete_broadcast.return_value = True

    await delete_broadcast(
        broadcast_id=1,
        service=mock_service,
        admin={"id": 1, "role": "admin"},
    )
    mock_service.delete_broadcast.assert_called_once_with(1)


@pytest.mark.asyncio
async def test_delete_broadcast_not_found():
    """When broadcast not found, raises 404."""
    mock_service = AsyncMock()
    mock_service.delete_broadcast.return_value = False

    with pytest.raises(HTTPException) as exc_info:
        await delete_broadcast(
            broadcast_id=99,
            service=mock_service,
            admin={"id": 1, "role": "admin"},
        )

    assert exc_info.value.status_code == 404
