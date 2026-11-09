import pytest
from httpx import AsyncClient, ASGITransport
import app.main as main_module
from app.api.deps import get_db_session
from app.infrastructure.db.session import Base
from app.infrastructure.db.models import MovieModel
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_filter_movies_sort_and_genre_slug_translation(engine, db_session: AsyncSession):
    """
    FILTER-002 & FILTER-003 Regression Test:
    1. FILTER-003: GET /api/v1/movies?sort=rating must return movies ordered by imdb_rating DESC.
       GET /api/v1/movies?sort=latest must return movies ordered by release_year DESC.
    2. FILTER-002: GET /api/v1/movies?genre=action must match movies with genres='Jangari'
       via genre slug-to-Uzbek mapping.
    """
    fastapi_app = main_module.app
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Insert movies with intentional IDs so ID ASC does not match rating DESC
    # Movie 1: low rating, newest year
    m1 = MovieModel(
        title="Movie Low Rating",
        code="m_s01",
        publish_status="published",
        imdb_rating=5.0,
        release_year=2024,
        genres="Komediya",
    )
    # Movie 2: medium rating, older year
    m2 = MovieModel(
        title="Movie Med Rating",
        code="m_s02",
        publish_status="published",
        imdb_rating=7.5,
        release_year=2018,
        genres="Jangari, Triller",
    )
    # Movie 3: top rating, oldest year
    m3 = MovieModel(
        title="Movie Top Rating",
        code="m_s03",
        publish_status="published",
        imdb_rating=9.2,
        release_year=2010,
        genres="Jangari, Fantastika",
    )
    db_session.add_all([m1, m2, m3])
    await db_session.commit()
    await db_session.refresh(m1)
    await db_session.refresh(m2)
    await db_session.refresh(m3)

    async def override_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db_session] = override_db

    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Assert Sort by Rating DESC
            resp_rating = await client.get("/api/v1/movies?sort=rating")
            assert resp_rating.status_code == 200, resp_rating.text
            items_rating = resp_rating.json()["items"]
            rating_ids = [m["id"] for m in items_rating]
            assert rating_ids == [m3.id, m2.id, m1.id], (
                f"Expected rating sort [m3({m3.id}), m2({m2.id}), m1({m1.id})], got {rating_ids}"
            )

            # 2. Assert Sort by Latest Year DESC
            resp_latest = await client.get("/api/v1/movies?sort=latest")
            assert resp_latest.status_code == 200, resp_latest.text
            items_latest = resp_latest.json()["items"]
            latest_ids = [m["id"] for m in items_latest]
            assert latest_ids == [m1.id, m2.id, m3.id], (
                f"Expected latest sort [m1({m1.id}), m2({m2.id}), m3({m3.id})], got {latest_ids}"
            )

            # 3. Assert English genre slug 'action' matches 'Jangari'
            resp_genre = await client.get("/api/v1/movies?genre=action")
            assert resp_genre.status_code == 200, resp_genre.text
            items_genre = resp_genre.json()["items"]
            genre_ids = [m["id"] for m in items_genre]
            assert m3.id in genre_ids and m2.id in genre_ids, (
                f"Expected m2({m2.id}) and m3({m3.id}) for genre=action, got {genre_ids}"
            )
            assert m1.id not in genre_ids
    finally:
        fastapi_app.dependency_overrides.pop(get_db_session, None)
