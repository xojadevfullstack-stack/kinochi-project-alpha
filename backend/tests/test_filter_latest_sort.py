import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from app.infrastructure.db.session import Base
from app.infrastructure.db.models import MovieModel, SeriesModel
from app.api.deps import get_db_session
import app.main as main_module
import datetime

@pytest.mark.asyncio
async def test_filter_latest_sort_movies_and_series(engine, db_session: AsyncSession):
    fastapi_app = main_module.app
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Insert test movies: m1 uploaded first, m2 uploaded second (latest addition)
    m1_uploaded_first = MovieModel(
        title="Movie Uploaded First (2025)",
        code="m_lat_01",
        publish_status="published",
        release_year=2025,
        imdb_rating=7.0,
        created_at=datetime.datetime(2026, 1, 1, 10, 0, 0)
    )
    m2_uploaded_second = MovieModel(
        title="Movie Uploaded Second (2022)",
        code="m_lat_02",
        publish_status="published",
        release_year=2022,
        imdb_rating=6.5,
        created_at=datetime.datetime(2026, 1, 2, 12, 0, 0)
    )
    db_session.add_all([m1_uploaded_first, m2_uploaded_second])
    await db_session.commit()
    await db_session.refresh(m1_uploaded_first)
    await db_session.refresh(m2_uploaded_second)

    async def override_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db_session] = override_db

    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/movies?sort=latest&limit=50")
            assert resp.status_code == 200, resp.text
            items = resp.json()["items"]
            test_ids = {m1_uploaded_first.id, m2_uploaded_second.id}
            returned_test_ids = [m["id"] for m in items if m["id"] in test_ids]
            
            # Expected order: m2 (uploaded second = latest addition) then m1
            expected_order = [m2_uploaded_second.id, m1_uploaded_first.id]
            assert returned_test_ids == expected_order, (
                f"Expected latest sort order {expected_order}, got {returned_test_ids}"
            )
    finally:
        fastapi_app.dependency_overrides.pop(get_db_session, None)
