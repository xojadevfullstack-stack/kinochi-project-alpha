import pytest
from unittest.mock import AsyncMock
from starlette.requests import Request
from fastapi import HTTPException
from app.api.v1.series import list_seasons


@pytest.mark.asyncio
async def test_f006_list_seasons_filters_published():
    """F-006 regression test: list_seasons must enforce publish_status='published'."""
    mock_service = AsyncMock()
    # When querying with publish_status='published' for a pending series, it returns None
    mock_service.get_series_by_id.return_value = None

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/series/123/seasons",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "app": None,
    }
    mock_request = Request(scope)

    with pytest.raises(HTTPException) as exc_info:
        await list_seasons(
            request=mock_request,
            series_id=123,
            service=mock_service
        )

    assert exc_info.value.status_code == 404
    # Crucial assertion: get_series_by_id MUST be called with publish_status='published'
    mock_service.get_series_by_id.assert_called_once_with(123, publish_status="published")
