import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
import app.main as main_module
from app.api.deps import get_db_session
from app.infrastructure.db.session import Base
from app.infrastructure.db.models import MovieModel, SeriesModel
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_filter_actors_filmography_only_marks_published_available(engine, db_session: AsyncSession):
    """
    FILTER-007 Regression Test:
    In GET /api/v1/actors/filmography, only movies and series with publish_status == 'published'
    may be marked is_available: True.
    Pending and draft movies must remain is_available: False so users don't encounter dead links/404s.
    """
    fastapi_app = main_module.app
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 1. Seed published movie, pending movie, draft series
    pub_movie = MovieModel(
        title="Oppenheimer",
        code="m_opp",
        publish_status="published",
        tmdb_id=872585,
    )
    pending_movie = MovieModel(
        title="Peaky Blinders Movie",
        code="m_pky",
        publish_status="pending",
        tmdb_id=999111,
    )
    draft_series = SeriesModel(
        title="Draft Actor Show",
        publish_status="draft",
        tmdb_id=888222,
    )
    db_session.add_all([pub_movie, pending_movie, draft_series])
    await db_session.commit()

    async def override_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db_session] = override_db

    mock_filmography = [
        {"tmdb_id": 872585, "title": "Oppenheimer", "release_year": 2023},
        {"tmdb_id": 999111, "title": "Peaky Blinders Movie", "release_year": 2025},
        {"tmdb_id": 888222, "title": "Draft Actor Show", "release_year": 2024},
    ]

    try:
        with patch("app.infrastructure.external.tmdb_client.tmdb_client.get_person_filmography", new=AsyncMock(return_value=mock_filmography)):
            transport = ASGITransport(app=fastapi_app)
            async with AsyncClient(transport=transport, base_url="http://test") as client:
                resp = await client.get("/api/v1/actors/2034/movies")
                assert resp.status_code == 200, resp.text
                movies = resp.json()["movies"]

                m_pub = next(m for m in movies if m["tmdb_id"] == 872585)
                m_pending = next(m for m in movies if m["tmdb_id"] == 999111)
                s_draft = next(m for m in movies if m["tmdb_id"] == 888222)

                # Published movie must be marked available
                assert m_pub["is_available"] is True
                assert m_pub["local_movie"] is not None

                # Pending movie must NOT be marked available
                assert m_pending["is_available"] is False, (
                    "Pending movie must NOT be marked is_available: True"
                )
                assert m_pending["local_movie"] is None

                # Draft series must NOT be marked available
                assert s_draft["is_available"] is False, (
                    "Draft series must NOT be marked is_available: True"
                )
                assert s_draft["local_movie"] is None
    finally:
        fastapi_app.dependency_overrides.pop(get_db_session, None)
