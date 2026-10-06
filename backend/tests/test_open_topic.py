import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.api.deps import get_current_admin
from app.domain.movies.entities import Movie


@pytest.mark.asyncio
async def test_open_movie_topic_success():
    app.dependency_overrides[get_current_admin] = lambda: {"username": "admin", "role": "admin"}

    mock_movie = Movie(
        id=10,
        title="Avatar",
        code="1234",
        release_year=2009,
        source_chat_id=None,
        source_topic_id=None,
    )

    with patch("app.api.v1.movies.get_movie_service") as mock_get_srv, \
         patch("app.core.config.settings.AUTO_TOPIC_CHAT_ID", -1001234567), \
         patch("app.api.v1.movies.telegram_client.create_forum_topic", new_callable=AsyncMock) as mock_create_topic, \
         patch("app.api.v1.movies.telegram_client.send_topic_message", new_callable=AsyncMock) as mock_send_msg, \
         patch("app.api.v1.movies.delete_cache_pattern", new_callable=AsyncMock):

        mock_srv = AsyncMock()
        mock_srv.get_movie.return_value = mock_movie
        mock_srv.get_movie_by_id.return_value = mock_movie
        mock_srv.update_movie.return_value = mock_movie
        mock_create_topic.return_value = 555
        mock_send_msg.return_value = 1001

        from app.api.deps import get_movie_service
        app.dependency_overrides[get_movie_service] = lambda: mock_srv

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/api/v1/movies/10/open-topic")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["topic_id"] == 555
            assert data["already_existed"] is False
            mock_create_topic.assert_called_once()
            mock_send_msg.assert_called_once()

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_open_movie_topic_already_existed():
    app.dependency_overrides[get_current_admin] = lambda: {"username": "admin", "role": "admin"}

    mock_movie = Movie(
        id=10,
        title="Avatar",
        code="1234",
        release_year=2009,
        source_chat_id=-1001234567,
        source_topic_id=777,
    )

    mock_srv = AsyncMock()
    mock_srv.get_movie.return_value = mock_movie
    mock_srv.get_movie_by_id.return_value = mock_movie

    from app.api.deps import get_movie_service
    app.dependency_overrides[get_movie_service] = lambda: mock_srv

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post("/api/v1/movies/10/open-topic")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["already_existed"] is True
        assert data["topic_id"] == 777

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_open_series_topic_success():
    app.dependency_overrides[get_current_admin] = lambda: {"username": "admin", "role": "admin"}

    from datetime import datetime
    from app.domain.series.entities import Series
    mock_series = Series(
        id=5,
        title="Breaking Bad",
        release_year=2008,
        source_id=None,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    with patch("app.core.config.settings.AUTO_TOPIC_CHAT_ID", -1001234567), \
         patch("app.api.v1.series.telegram_client.create_forum_topic", new_callable=AsyncMock) as mock_create_topic, \
         patch("app.api.v1.series.telegram_client.send_topic_message", new_callable=AsyncMock) as mock_send_msg, \
         patch("app.api.v1.series.delete_cache_pattern", new_callable=AsyncMock), \
         patch("app.infrastructure.db.repositories.source_repository.SourceRepository.create_source", new_callable=AsyncMock) as mock_create_source:

        mock_srv = AsyncMock()
        mock_srv.get_series_by_id.return_value = mock_series
        mock_srv.update_series.return_value = mock_series
        mock_create_topic.return_value = 888
        mock_send_msg.return_value = 2002

        from unittest.mock import MagicMock
        mock_source = MagicMock()
        mock_source.id = 99
        mock_create_source.return_value = mock_source

        from app.api.deps import get_series_service, get_db_session
        app.dependency_overrides[get_series_service] = lambda: mock_srv

        mock_session = AsyncMock()
        async def override_get_db():
            yield mock_session
        app.dependency_overrides[get_db_session] = override_get_db

        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            resp = await ac.post("/api/v1/series/5/open-topic")
            assert resp.status_code == 200
            data = resp.json()
            assert data["success"] is True
            assert data["topic_id"] == 888
            assert data["source_id"] == 99
            mock_create_topic.assert_called_once()
            mock_send_msg.assert_called_once()

    app.dependency_overrides.clear()
