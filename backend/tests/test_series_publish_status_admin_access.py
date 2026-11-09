import pytest
from unittest.mock import AsyncMock, MagicMock
from starlette.requests import Request
from fastapi import HTTPException
from app.api.v1.series import list_seasons, get_season, list_episodes


@pytest.mark.asyncio
async def test_list_seasons_passes_publish_status():
    """list_seasons should accept publish_status from resolve_publish_status (e.g. None for all, or pending)."""
    mock_service = AsyncMock()
    mock_series = MagicMock()
    mock_series.seasons = [{"id": 1, "season_number": 1}]
    mock_service.get_series_by_id.return_value = mock_series

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/series/10/seasons",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "app": None,
    }
    mock_request = Request(scope)

    # Admin passes publish_status=None (meaning all statuses)
    result = await list_seasons(
        request=mock_request,
        series_id=10,
        publish_status=None,
        service=mock_service,
    )

    assert result == [{"id": 1, "season_number": 1}]
    mock_service.get_series_by_id.assert_called_once_with(10, publish_status=None)


@pytest.mark.asyncio
async def test_get_season_passes_publish_status():
    """get_season should accept publish_status and pass it to get_season_by_id."""
    mock_service = AsyncMock()
    mock_season = MagicMock()
    mock_season.id = 5
    mock_service.get_season_by_id.return_value = mock_season

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/series/seasons/5",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "app": None,
    }
    mock_request = Request(scope)

    result = await get_season(
        request=mock_request,
        season_id=5,
        publish_status="pending",
        service=mock_service,
    )

    assert result == mock_season
    mock_service.get_season_by_id.assert_called_once_with(5, publish_status="pending")


@pytest.mark.asyncio
async def test_list_episodes_passes_publish_status():
    """list_episodes should accept publish_status and pass it to get_season_by_id."""
    mock_service = AsyncMock()
    mock_season = MagicMock()
    mock_season.episodes = [{"id": 101, "episode_number": 1}]
    mock_service.get_season_by_id.return_value = mock_season

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/series/seasons/5/episodes",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "app": None,
    }
    mock_request = Request(scope)

    result = await list_episodes(
        request=mock_request,
        season_id=5,
        publish_status=None,
        service=mock_service,
    )

    assert result == [{"id": 101, "episode_number": 1}]
    mock_service.get_season_by_id.assert_called_once_with(5, publish_status=None)
