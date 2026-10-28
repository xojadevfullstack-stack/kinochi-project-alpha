import pytest
from unittest.mock import AsyncMock
from starlette.requests import Request
from fastapi import HTTPException
from app.api.v1.series import get_series


@pytest.mark.asyncio
async def test_get_series_by_numeric_id():
    """Numeric identifier should call get_series_by_id."""
    mock_service = AsyncMock()
    mock_service.get_series_by_id.return_value = {"id": 1008, "title": "Chernobil"}

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/series/1008",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "app": None,
    }
    mock_request = Request(scope)

    result = await get_series(
        request=mock_request,
        series_id_or_code="1008",
        publish_status="published",
        service=mock_service,
    )

    assert result["id"] == 1008
    mock_service.get_series_by_id.assert_called_once_with(1008, publish_status="published")


@pytest.mark.asyncio
async def test_get_series_by_episode_or_alphanumeric_code():
    """Non-numeric code should call get_series_by_code."""
    mock_service = AsyncMock()
    mock_service.get_series_by_code.return_value = {"id": 1008, "title": "Chernobil"}

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/series/gb3SGSCj",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "app": None,
    }
    mock_request = Request(scope)

    result = await get_series(
        request=mock_request,
        series_id_or_code="gb3SGSCj",
        publish_status="published",
        service=mock_service,
    )

    assert result["id"] == 1008
    mock_service.get_series_by_code.assert_called_once_with("gb3SGSCj", publish_status="published")


@pytest.mark.asyncio
async def test_get_series_not_found_raises_404():
    """When both id and code fail, raises 404."""
    mock_service = AsyncMock()
    mock_service.get_series_by_id.return_value = None
    mock_service.get_series_by_code.return_value = None

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/series/unknown_code",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "app": None,
    }
    mock_request = Request(scope)

    with pytest.raises(HTTPException) as exc_info:
        await get_series(
            request=mock_request,
            series_id_or_code="unknown_code",
            publish_status="published",
            service=mock_service,
        )

    assert exc_info.value.status_code == 404
