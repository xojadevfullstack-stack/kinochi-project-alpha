import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import Base
from app.infrastructure.db.models import MovieModel, SeriesModel
from app.api.deps import get_db_session
import app.main as main_module

@pytest.mark.asyncio
async def test_filter_latest_sort_movies_and_series(engine, db_session: AsyncSession):
    fastapi_app = main_module.app
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Insert test movies with different years and IDs
    m_old_high_id = MovieModel(
        title="Movie 2022 NewID",
        code="m_lat_01",
        publish_status="published",
        release_year=2022,
        imdb_rating=7.0
    )
    m_new_low_id = MovieModel(
        title="Movie 2025 LowID",
        code="m_lat_02",
        publish_status="published",
        release_year=2025,
        imdb_rating=6.5
    )
    m_same_year_new = MovieModel(
        title="Movie 2025 HighID",
        code="m_lat_03",
        publish_status="published",
        release_year=2025,
        imdb_rating=8.0
    )
    db_session.add_all([m_old_high_id, m_new_low_id, m_same_year_new])
    await db_session.commit()
    await db_session.refresh(m_old_high_id)
    await db_session.refresh(m_new_low_id)
    await db_session.refresh(m_same_year_new)

    async def override_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db_session] = override_db

    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/movies?sort=latest&limit=50")
            assert resp.status_code == 200, resp.text
            items = resp.json()["items"]
            test_ids = {m_old_high_id.id, m_new_low_id.id, m_same_year_new.id}
            returned_test_ids = [m["id"] for m in items if m["id"] in test_ids]
            
            # Expected order: 2025 HighID, 2025 LowID, 2022 NewID
            expected_order = [m_same_year_new.id, m_new_low_id.id, m_old_high_id.id]
            assert returned_test_ids == expected_order, (
                f"Expected latest sort order {expected_order}, got {returned_test_ids}"
            )
    finally:
        fastapi_app.dependency_overrides.pop(get_db_session, None)
