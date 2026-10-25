import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import BackgroundTasks

from app.application.broadcasts.service import BroadcastService
from app.domain.broadcasts.entities import Broadcast, BroadcastStatus

@pytest.fixture
def b_repo():
    return AsyncMock()

@pytest.fixture
def u_repo():
    return AsyncMock()

@pytest.fixture
def service(b_repo, u_repo):
    return BroadcastService(b_repo, u_repo)


@pytest.mark.asyncio
async def test_create_broadcast_success(service, b_repo, u_repo):
    # Setup
    u_repo.list_users.return_value = ([], 150)
    
    expected_broadcast = Broadcast(
        id=1,
        message_text="Hello",
        status=BroadcastStatus.DRAFT,
        total_recipients=150
    )
    b_repo.create.return_value = expected_broadcast
    
    # Action
    result = await service.create_broadcast(message_text="Hello")
    
    # Assert
    assert result.id == 1
    assert result.total_recipients == 150
    u_repo.list_users.assert_called_once()
    b_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_create_broadcast_with_media_and_buttons(service, b_repo, u_repo):
    u_repo.list_users.return_value = ([], 200)

    expected = Broadcast(
        id=2,
        message_text="Pre-order movie now!",
        status=BroadcastStatus.DRAFT,
        media_type="photo",
        media_url="https://example.com/poster.jpg",
        button_text="Ko'rish",
        button_url="https://kinochi.uz/movie/99",
        total_recipients=200,
    )
    b_repo.create.return_value = expected

    result = await service.create_broadcast(
        message_text="Pre-order movie now!",
        media_type="photo",
        media_url="https://example.com/poster.jpg",
        button_text="Ko'rish",
        button_url="https://kinochi.uz/movie/99",
    )

    assert result.media_type == "photo"
    assert result.media_url == "https://example.com/poster.jpg"
    assert result.button_text == "Ko'rish"
    assert result.button_url == "https://kinochi.uz/movie/99"
    b_repo.create.assert_called_once()


@pytest.mark.asyncio
async def test_start_broadcast_success(service, b_repo):
    # Setup
    broadcast = Broadcast(
        id=1,
        message_text="Hello",
        status=BroadcastStatus.DRAFT,
        total_recipients=150
    )
    b_repo.get_by_id.return_value = broadcast
    
    mock_bg_tasks = MagicMock(spec=BackgroundTasks)
    
    expected_broadcast = Broadcast(
        id=1,
        message_text="Hello",
        status=BroadcastStatus.SENDING,
        total_recipients=150
    )
    b_repo.update_status.return_value = expected_broadcast
    
    # Action
    result = await service.start_broadcast(id=1, background_tasks=mock_bg_tasks)
    
    # Assert
    assert result.status == BroadcastStatus.SENDING
    mock_bg_tasks.add_task.assert_called_once()
    b_repo.update_status.assert_called_once_with(1, BroadcastStatus.SENDING)


@pytest.mark.asyncio
async def test_start_broadcast_with_media(service, b_repo):
    broadcast = Broadcast(
        id=3,
        message_text="Watch new trailer",
        status=BroadcastStatus.DRAFT,
        media_type="video",
        media_url="https://example.com/trailer.mp4",
        button_text="Saytda ko'rish",
        button_url="https://kinochi.uz",
        total_recipients=500
    )
    b_repo.get_by_id.return_value = broadcast
    mock_bg_tasks = MagicMock(spec=BackgroundTasks)

    await service.start_broadcast(id=3, background_tasks=mock_bg_tasks)

    mock_bg_tasks.add_task.assert_called_once()
    args, kwargs = mock_bg_tasks.add_task.call_args
    assert kwargs["broadcast_id"] == 3
    assert kwargs["message_text"] == "Watch new trailer"
    assert kwargs["media_type"] == "video"
    assert kwargs["media_url"] == "https://example.com/trailer.mp4"
    assert kwargs["button_text"] == "Saytda ko'rish"
    assert kwargs["button_url"] == "https://kinochi.uz"


@pytest.mark.asyncio
async def test_start_broadcast_not_found(service, b_repo):
    # Setup
    b_repo.get_by_id.return_value = None
    mock_bg_tasks = MagicMock(spec=BackgroundTasks)
    
    # Action
    result = await service.start_broadcast(id=999, background_tasks=mock_bg_tasks)
    
    # Assert
    assert result is None
    b_repo.update_status.assert_not_called()
    mock_bg_tasks.add_task.assert_not_called()
