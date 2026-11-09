import pytest
from httpx import AsyncClient, ASGITransport
import app.main as main_module
from app.api.deps import get_db_session
from app.infrastructure.db.session import Base
from app.infrastructure.db.models import SeriesModel
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_filter_series_sort_by_rating_and_latest(engine, db_session: AsyncSession):
    """
    FILTER-004 Regression Test:
    GET /api/v1/series?sort=rating must return series sorted by imdb_rating DESC.
    GET /api/v1/series?sort=latest must return series sorted by release_year DESC.
    """
    fastapi_app = main_module.app
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Insert 3 series with ascending IDs such that ID ASC differs from rating DESC
    s1 = SeriesModel(
        title="Series Low Rating",
        publish_status="published",
        imdb_rating=5.5,
        release_year=2024,
    )
    s2 = SeriesModel(
        title="Series Med Rating",
        publish_status="published",
        imdb_rating=7.8,
        release_year=2019,
    )
    s3 = SeriesModel(
        title="Series Top Rating",
        publish_status="published",
        imdb_rating=9.1,
        release_year=2012,
    )
    db_session.add_all([s1, s2, s3])
    await db_session.commit()
    await db_session.refresh(s1)
    await db_session.refresh(s2)
    await db_session.refresh(s3)

    async def override_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db_session] = override_db

    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Assert Sort by Rating DESC
            resp_rating = await client.get("/api/v1/series?sort=rating")
            assert resp_rating.status_code == 200, resp_rating.text
            items_rating = resp_rating.json()["items"]
            rating_ids = [s["id"] for s in items_rating]
            assert rating_ids == [s3.id, s2.id, s1.id], (
                f"Expected rating sort [s3({s3.id}), s2({s2.id}), s1({s1.id})], got {rating_ids}"
            )

            # 2. Assert Sort by Latest Year DESC
            resp_latest = await client.get("/api/v1/series?sort=latest")
            assert resp_latest.status_code == 200, resp_latest.text
            items_latest = resp_latest.json()["items"]
            latest_ids = [s["id"] for s in items_latest]
            assert latest_ids == [s1.id, s2.id, s3.id], (
                f"Expected latest sort [s1({s1.id}), s2({s2.id}), s3({s3.id})], got {latest_ids}"
            )
    finally:
        fastapi_app.dependency_overrides.pop(get_db_session, None)
