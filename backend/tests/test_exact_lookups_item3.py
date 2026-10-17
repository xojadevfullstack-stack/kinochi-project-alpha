"""Tests for Item 3: Exact lookups and ambiguous topic rejection in movies and series."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from app.main import app
from app.infrastructure.db.repositories.movie_repo import MovieRepositoryImpl
from app.infrastructure.db.repositories.series_repository import SeriesRepository
from app.api.deps import get_db_session, get_current_admin


@pytest.mark.asyncio
async def test_movie_repo_get_by_source_topic_id_mandatory():
    """movie_repo.get_by_source topic_id berilmasa ValueError tashlashi shart."""
    session = AsyncMock(spec=AsyncSession)
    repo = MovieRepositoryImpl(session)
    with pytest.raises(ValueError, match="topic_id is mandatory"):
        await repo.get_by_source(chat_id=123, topic_id=None)


@pytest.mark.asyncio
async def test_series_repo_get_series_by_source_topic_id_mandatory():
    """series_repo.get_series_by_source topic_id berilmasa ValueError tashlashi shart."""
    session = AsyncMock(spec=AsyncSession)
    repo = SeriesRepository(session)
    with pytest.raises(ValueError, match="topic_id is mandatory"):
        await repo.get_series_by_source(chat_id=123, topic_id=None)


@pytest.mark.asyncio
async def test_movie_repo_ambiguous_multiple_movies_raises():
    """Bitta topic_id ga bir nechta kino to'g'ri kelsa ValueError tashlashi kerak."""
    session = AsyncMock(spec=AsyncSession)
    repo = MovieRepositoryImpl(session)

    mock_movie1 = MagicMock()
    mock_movie2 = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [mock_movie1, mock_movie2]
    exec_res = MagicMock()
    exec_res.scalars.return_value = scalars_mock

    empty_res = MagicMock()
    empty_res.scalars.return_value.all.return_value = []
    session.execute.side_effect = [exec_res, empty_res]

    with pytest.raises(ValueError, match="Ambiguous topic: multiple entities"):
        await repo.get_by_source(chat_id=-1001, topic_id=55)


@pytest.mark.asyncio
async def test_series_repo_ambiguous_multiple_series_raises():
    """Bitta topic_id ga bir nechta serial to'g'ri kelsa ValueError tashlashi kerak."""
    session = AsyncMock(spec=AsyncSession)
    repo = SeriesRepository(session)

    mock_s1 = MagicMock()
    mock_s2 = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = [mock_s1, mock_s2]
    exec_res = MagicMock()
    exec_res.scalars.return_value = scalars_mock

    empty_res = MagicMock()
    empty_res.scalars.return_value.all.return_value = []
    session.execute.side_effect = [exec_res, empty_res]

    with pytest.raises(ValueError, match="Ambiguous topic: multiple entities"):
        await repo.get_series_by_source(chat_id=-1001, topic_id=55)


@pytest.mark.asyncio
async def test_movies_by_source_endpoint_requires_topic_id():
    """GET /api/v1/movies/by-source endpointida topic_id majburiy (422 bo'lishi kerak)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/movies/by-source?chat_id=-100123")
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_series_by_source_endpoint_requires_topic_id():
    """GET /api/v1/series/by-source endpointida topic_id majburiy (422 bo'lishi kerak)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/series/by-source?chat_id=-100123")
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.asyncio
async def test_movies_by_source_rejects_ambiguous_with_409_and_rejected_item():
    """Agar topic bir vaqtda ham kino ham serialga tegishli bo'lsa, 409 qaytadi va rejection yoziladi."""
    mock_session = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_db_session] = lambda: mock_session

    try:
        # 1 ta kino va 1 ta serial qaytadigan qilib mocklaymiz
        mock_movie = MagicMock()
        mock_movie.id = 1
        mock_movie.title = "Kino 1"
        mock_movie.code = "101"
        mock_movie.release_year = 2024
        mock_movie.source_chat_id = -1001
        mock_movie.source_topic_id = 99
        mock_movie.categories = []
        mock_movie.translations = []
        mock_movie.pages = []

        mock_series_source = MagicMock()
        mock_series_source.id = 1
        mock_series_source.chat_id = -1001
        mock_series_source.topic_id = 99

        # execute ketma-ket chaqiriladi: 1-res_m, 2-res_s, 3-res_rej
        res_m = MagicMock()
        res_m.scalars.return_value.all.return_value = [mock_movie]

        res_s = MagicMock()
        res_s.scalars.return_value.all.return_value = [mock_series_source]

        res_rej = MagicMock()
        res_rej.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [res_m, res_s, res_rej]

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/movies/by-source?chat_id=-1001&topic_id=99")
            assert resp.status_code == status.HTTP_409_CONFLICT
            data = resp.json()
            assert data["detail"]["defect"] == "ambiguous_topic"
            # Session commit chaqirilganini (rejection yozilganini) tekshiramiz
            assert mock_session.commit.called
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_series_by_source_rejects_ambiguous_with_409_and_rejected_item():
    """Agar topic bir vaqtda ham serial ham kinoga tegishli bo'lsa, /series/by-source 409 qaytaradi."""
    mock_session = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_db_session] = lambda: mock_session

    try:
        mock_series = MagicMock()
        mock_series.id = 1
        mock_series.title = "Serial 1"

        mock_movie = MagicMock()
        mock_movie.id = 2

        # 1-res_s (series), 2-res_m (movies), 3-res_rej (rejected_items)
        res_s = MagicMock()
        res_s.scalars.return_value.all.return_value = [mock_series]

        res_m = MagicMock()
        res_m.scalars.return_value.all.return_value = [mock_movie]

        res_rej = MagicMock()
        res_rej.scalar_one_or_none.return_value = None

        mock_session.execute.side_effect = [res_s, res_m, res_rej]

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/series/by-source?chat_id=-1001&topic_id=99")
            assert resp.status_code == status.HTTP_409_CONFLICT
            data = resp.json()
            assert data["detail"]["defect"] == "ambiguous_topic"
            assert mock_session.commit.called
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_movies_by_source_commits_independent_session_before_exception():
    """Noaniq topicda mustaqil sessiya (async_session_factory) orqali rejected_items commit qilinadi."""
    mock_db = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_db_session] = lambda: mock_db

    independent_session = AsyncMock(spec=AsyncSession)
    res_rej = MagicMock()
    res_rej.scalar_one_or_none.return_value = None
    independent_session.execute.return_value = res_rej

    class MockSessionFactory:
        def __call__(self):
            return self
        async def __aenter__(self):
            return independent_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_factory = MockSessionFactory()

    try:
        mock_movie1 = MagicMock()
        mock_movie2 = MagicMock()
        res_m = MagicMock()
        res_m.scalars.return_value.all.return_value = [mock_movie1, mock_movie2]

        res_s = MagicMock()
        res_s.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [res_m, res_s]

        with patch("app.api.v1.movies.async_session_factory", mock_factory):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/movies/by-source?chat_id=-1001&topic_id=99")
                assert resp.status_code == status.HTTP_409_CONFLICT
                # Mustaqil sessiyada commit chaqirilgan bo'lishi shart
                assert independent_session.commit.called
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_series_by_source_commits_independent_session_before_exception():
    """Serial bo'yicha noaniq topicda mustaqil sessiya commit qilinishi shart."""
    mock_db = AsyncMock(spec=AsyncSession)
    app.dependency_overrides[get_db_session] = lambda: mock_db

    independent_session = AsyncMock(spec=AsyncSession)
    res_rej = MagicMock()
    res_rej.scalar_one_or_none.return_value = None
    independent_session.execute.return_value = res_rej

    class MockSessionFactory:
        def __call__(self):
            return self
        async def __aenter__(self):
            return independent_session
        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    mock_factory = MockSessionFactory()

    try:
        mock_s1 = MagicMock()
        mock_s2 = MagicMock()
        res_s = MagicMock()
        res_s.scalars.return_value.all.return_value = [mock_s1, mock_s2]

        res_m = MagicMock()
        res_m.scalars.return_value.all.return_value = []

        mock_db.execute.side_effect = [res_s, res_m]

        with patch("app.api.v1.series.async_session_factory", mock_factory):
            transport = ASGITransport(app=app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/series/by-source?chat_id=-1001&topic_id=99")
                assert resp.status_code == status.HTTP_409_CONFLICT
                assert independent_session.commit.called
    finally:
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_movie_repo_rejects_topic_present_as_both_movie_and_series():
    """movie_repo.get_by_source bitta topicda ham kino ham serial mavjud bo'lsa rad etadi."""
    session = AsyncMock(spec=AsyncSession)
    repo = MovieRepositoryImpl(session)

    mock_movie = MagicMock()
    res_m = MagicMock()
    res_m.scalars.return_value.all.return_value = [mock_movie]

    mock_series_source = MagicMock()
    res_s = MagicMock()
    res_s.scalars.return_value.all.return_value = [mock_series_source]

    session.execute.side_effect = [res_m, res_s]

    with pytest.raises(ValueError, match="Ambiguous topic: multiple entities"):
        await repo.get_by_source(chat_id=-1001, topic_id=55)


@pytest.mark.asyncio
async def test_series_repo_rejects_topic_present_as_both_series_and_movie():
    """series_repo.get_series_by_source bitta topicda ham serial ham kino mavjud bo'lsa rad etadi."""
    session = AsyncMock(spec=AsyncSession)
    repo = SeriesRepository(session)

    mock_series = MagicMock()
    res_s = MagicMock()
    res_s.scalars.return_value.all.return_value = [mock_series]

    mock_movie = MagicMock()
    res_m = MagicMock()
    res_m.scalars.return_value.all.return_value = [mock_movie]

    session.execute.side_effect = [res_s, res_m]

    with pytest.raises(ValueError, match="Ambiguous topic: multiple entities"):
        await repo.get_series_by_source(chat_id=-1001, topic_id=55)
