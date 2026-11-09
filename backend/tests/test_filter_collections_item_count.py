import pytest
from httpx import AsyncClient, ASGITransport
import app.main as main_module
from app.api.deps import get_db_session
from app.infrastructure.db.session import Base
from app.infrastructure.db.models import CollectionModel, CollectionItemModel, MovieModel, SeriesModel
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_filter_collections_item_count_excludes_unpublished(engine, db_session: AsyncSession):
    """
    FILTER-001 Regression Test:
    Collections list endpoint (/api/v1/collections) must ONLY count items whose
    referenced movie or series is published (publish_status == 'published').
    Pending, draft, or orphaned items must NOT be counted in items_count or included in deck posters.
    """
    fastapi_app = main_module.app
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 1. Create a test collection
    collection = CollectionModel(
        name="Marvel Cinematic Universe",
        slug="mcu-test",
        is_franchise=True,
        is_active=True,
        sort_order=1,
    )
    db_session.add(collection)
    await db_session.commit()
    await db_session.refresh(collection)

    # 2. Create 1 published movie, 1 pending movie, 1 draft series
    pub_movie = MovieModel(
        title="Iron Man",
        code="m001",
        publish_status="published",
        poster_url="https://image.tmdb.org/ironman.jpg",
    )
    pending_movie = MovieModel(
        title="Spider-Man 4",
        code="m002",
        publish_status="pending",
        poster_url="https://image.tmdb.org/spiderman4_pending.jpg",
    )
    draft_series = SeriesModel(
        title="Secret Invasion",
        publish_status="draft",
        poster_url="https://image.tmdb.org/secret_invasion_draft.jpg",
    )
    db_session.add_all([pub_movie, pending_movie, draft_series])
    await db_session.commit()
    await db_session.refresh(pub_movie)
    await db_session.refresh(pending_movie)
    await db_session.refresh(draft_series)

    # 3. Link all 3 items to the collection
    item_pub = CollectionItemModel(
        collection_id=collection.id,
        movie_id=pub_movie.id,
        chronological_order=1,
        release_order=1,
    )
    item_pending = CollectionItemModel(
        collection_id=collection.id,
        movie_id=pending_movie.id,
        chronological_order=2,
        release_order=2,
    )
    item_draft = CollectionItemModel(
        collection_id=collection.id,
        series_id=draft_series.id,
        chronological_order=3,
        release_order=3,
    )
    db_session.add_all([item_pub, item_pending, item_draft])
    await db_session.commit()

    # 4. Dependency override
    async def override_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db_session] = override_db

    try:
        transport = ASGITransport(app=fastapi_app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get("/api/v1/collections")
            assert resp.status_code == 200, resp.text
            data = resp.json()

            col_data = next((c for c in data if c["id"] == collection.id), None)
            assert col_data is not None, "Created collection not found in response"

            # TRUTH: Only 1 published item exists.
            # RED assertion: currently code counts all 3 items, returning items_count=3.
            assert col_data["items_count"] == 1, (
                f"Expected items_count=1 (only published items), got {col_data['items_count']}"
            )

            # Deck posters must not include pending or draft posters
            assert "https://image.tmdb.org/spiderman4_pending.jpg" not in col_data["posters"]
            assert "https://image.tmdb.org/secret_invasion_draft.jpg" not in col_data["posters"]
    finally:
        fastapi_app.dependency_overrides.pop(get_db_session, None)
