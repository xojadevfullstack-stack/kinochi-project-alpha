import pytest
import re
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.infrastructure.db.session import Base
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.category import CategoryModel
from app.infrastructure.db.repositories.movie_repo import MovieRepositoryImpl

@pytest.mark.asyncio
async def test_guest_issue_001_movie_search_no_name_error():
    """GUEST-ISSUE-001: movie_repo.search_by_title must NOT crash with NameError (re must be imported)."""
    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    import app.core.cache as cache_module
    cache_module._memory_cache.clear()
    async with session_factory() as session:
        # Seed one movie
        movie = MovieModel(
            title="Avatar: Suv Yo'li",
            code="AVTR01",
            publish_status="published",
        )
        session.add(movie)
        await session.commit()

        repo = MovieRepositoryImpl(session)
        # This will trigger line 341 in movie_repo.py where re.split is called
        items, total = await repo.search_by_title("Avatar", skip=0, limit=10)
        assert total >= 1
        assert items[0].title == "Avatar: Suv Yo'li"
    
    await test_engine.dispose()


@pytest.mark.asyncio
async def test_guest_issue_002_collections_no_n_plus_one():
    """GUEST-ISSUE-002: GET /api/v1/collections must eliminate N+1 queries.
    Fetching 5 collections must execute O(1) queries (<= 4 queries total), not 1 + 2*N queries.
    """
    from httpx import AsyncClient, ASGITransport
    from sqlalchemy import event
    import app.main as main_module
    from app.api.deps import get_db_session
    from app.infrastructure.db.models import CollectionModel, CollectionItemModel, MovieModel

    test_engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    import app.core.cache as cache_module
    cache_module._memory_cache.clear()

    # Seed 5 collections, each with 2 items
    async with session_factory() as session:
        for i in range(1, 6):
            col = CollectionModel(
                name=f"Collection {i}",
                slug=f"col-{i}",
                is_franchise=True,
                is_active=True,
                sort_order=i,
            )
            session.add(col)
            await session.flush()

            m1 = MovieModel(title=f"Movie {i}-1", code=f"M{i}1", publish_status="published", poster_url=f"http://img/{i}1.jpg")
            m2 = MovieModel(title=f"Movie {i}-2", code=f"M{i}2", publish_status="published", poster_url=f"http://img/{i}2.jpg")
            session.add_all([m1, m2])
            await session.flush()

            session.add_all([
                CollectionItemModel(collection_id=col.id, movie_id=m1.id, chronological_order=1),
                CollectionItemModel(collection_id=col.id, movie_id=m2.id, chronological_order=2),
            ])
        await session.commit()

    captured_queries = []
    def track_query(conn, cursor, statement, parameters, context, executemany):
        captured_queries.append(statement)

    event.listen(test_engine.sync_engine, "before_cursor_execute", track_query)

    async def override_db():
        async with session_factory() as session:
            yield session

    app = main_module.app
    app.dependency_overrides[get_db_session] = override_db

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            captured_queries.clear()
            resp = await ac.get("/api/v1/collections")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data) == 5
            # Before optimization: 1 (select collections) + 5*(count) + 5*(items) + 10*(selectinload) = 21 queries!
            # After optimization: <= 4 queries total (O(1)).
            assert len(captured_queries) <= 4, (
                f"N+1 query bottleneck detected! Expected <= 4 DB queries, but executed {len(captured_queries)} queries."
            )
    finally:
        event.remove(test_engine.sync_engine, "before_cursor_execute", track_query)
        app.dependency_overrides.clear()
        import app.core.cache as cache_module
        cache_module._memory_cache.clear()
        await test_engine.dispose()

