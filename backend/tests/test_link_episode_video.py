import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.deps import get_admin_or_bot, get_series_service, get_db_session
from app.domain.series.entities import Episode


@pytest.mark.asyncio
async def test_link_episode_video_success():
    app.dependency_overrides[get_admin_or_bot] = lambda: {"username": "bot", "role": "bot"}

    from datetime import datetime, timezone
    mock_ep = Episode(
        id=14049,
        season_id=1237,
        episode_number=12,
        code="c_14049",
        display_code="S2-CH12",
        title="12-qism",
        created_at=datetime.now(timezone.utc),
        translations=[]
    )

    mock_service = AsyncMock()
    mock_service.link_episode_video_from_message.return_value = mock_ep
    app.dependency_overrides[get_series_service] = lambda: mock_service

    mock_db = AsyncMock()
    # Mock ep_model, season_model, series_model
    mock_ep_model = MagicMock()
    mock_ep_model.id = 14049
    mock_ep_model.season_id = 1237
    mock_ep_model.title = "12-qism"

    mock_season_model = MagicMock()
    mock_season_model.id = 1237
    mock_season_model.series_id = 997

    mock_series_model = MagicMock()
    mock_series_model.id = 997
    mock_series_model.publish_status = "pending"

    async def mock_get(model, ident):
        from app.infrastructure.db.models.series import EpisodeModel, SeasonModel, SeriesModel
        if model is EpisodeModel:
            return mock_ep_model
        elif model is SeasonModel:
            return mock_season_model
        elif model is SeriesModel:
            return mock_series_model
        return None

    mock_db.get = AsyncMock(side_effect=mock_get)
    mock_db.commit = AsyncMock()

    app.dependency_overrides[get_db_session] = lambda: mock_db

    with patch("app.api.v1.series.delete_cache_pattern", new_callable=AsyncMock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/api/v1/series/episodes/14049/link-video", json={
                "message_id": 99999,
                "language": "O'zbekcha",
                "telegram_file_id": "BAACAgIAAxkBAAE12345"
            })
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
            data = resp.json()
            assert data["id"] == 14049
            assert data["code"] == "c_14049"

    app.dependency_overrides.clear()
