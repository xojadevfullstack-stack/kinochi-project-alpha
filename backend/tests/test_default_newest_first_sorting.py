import pytest
from httpx import AsyncClient, ASGITransport
import app.main as main_module
from app.api.deps import get_db_session
from app.infrastructure.db.session import Base
from app.infrastructure.db.models import SeriesModel, MovieModel, PageModel
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_default_sort_returns_newest_first(engine, db_session: AsyncSession):
    """
    Default sort gate:
    GET /api/v1/series (without explicit sort) MUST return series newest first (id DESC).
    GET /api/v1/movies (without explicit sort) MUST return movies newest first (id DESC).
    """
    fastapi_app = main_module.app
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 1. Insert 3 series in chronological order
    s1 = SeriesModel(title="Series Oldest", publish_status="published")
    s2 = SeriesModel(title="Series Middle", publish_status="published")
    s3 = SeriesModel(title="Series Newest", publish_status="published")
    db_session.add_all([s1, s2, s3])

    # 2. Insert 3 movies in chronological order
    m1 = MovieModel(title="Movie Oldest", publish_status="published", code="mov_old1")
    m2 = MovieModel(title="Movie Middle", publish_status="published", code="mov_mid2")
    m3 = MovieModel(title="Movie Newest", publish_status="published", code="mov_new3")
    db_session.add_all([m1, m2, m3])

    await db_session.commit()
    await db_session.refresh(s1)
    await db_session.refresh(s2)
    await db_session.refresh(s3)
    await db_session.refresh(m1)
    await db_session.refresh(m2)
    await db_session.refresh(m3)

    async def override_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db_session] = override_db

    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            target_series_ids = {s1.id, s2.id, s3.id}
            target_movie_ids = {m1.id, m2.id, m3.id}

            # Test Series Default Ordering
            resp_s = await client.get("/api/v1/series")
            assert resp_s.status_code == 200, resp_s.text
            items_s = resp_s.json()["items"]
            result_s_ids = [s["id"] for s in items_s if s["id"] in target_series_ids]
            assert result_s_ids == [s3.id, s2.id, s1.id], (
                f"Expected series newest-first [s3({s3.id}), s2({s2.id}), s1({s1.id})], got {result_s_ids}"
            )

            # Test Movies Default Ordering
            resp_m = await client.get("/api/v1/movies")
            assert resp_m.status_code == 200, resp_m.text
            items_m = resp_m.json()["items"]
            result_m_ids = [m["id"] for m in items_m if m["id"] in target_movie_ids]
            assert result_m_ids == [m3.id, m2.id, m1.id], (
                f"Expected movies newest-first [m3({m3.id}), m2({m2.id}), m1({m1.id})], got {result_m_ids}"
            )
    finally:
        fastapi_app.dependency_overrides.pop(get_db_session, None)
