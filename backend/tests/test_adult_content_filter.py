import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.main import app
from app.api.deps import get_db_session
from app.api.limiter import limiter
from app.infrastructure.db.session import Base
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.series import SeriesModel
from app.infrastructure.db.models.category import CategoryModel


@pytest.fixture(autouse=True)
def disable_limiter():
    limiter.enabled = False
    yield
    limiter.enabled = True


@pytest.mark.asyncio
async def test_include_adult_false_excludes_18plus_movies_series_and_live_search(monkeypatch):
    # Disable Redis cache so SQL queries execute directly
    import app.api.v1.movies as movies_api
    import app.api.v1.series as series_api
    import app.api.v1.search as search_api

    async def no_cache(*args, **kwargs):
        return None

    async def no_set(*args, **kwargs):
        return None

    for mod in (movies_api, series_api, search_api):
        monkeypatch.setattr(mod, "get_cache", no_cache)
        monkeypatch.setattr(mod, "set_cache", no_set)

    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with session_factory() as session:
        cat_18 = CategoryModel(name="18+ Kattalar", slug="18-plus")
        cat_action = CategoryModel(name="Jangari", slug="jangari")
        session.add_all([cat_18, cat_action])
        await session.flush()

        m_safe = MovieModel(
            title="Safe Hero Movie",
            code="SAFE1",
            publish_status="published",
            is_18_plus=False,
            genres="Jangari",
        )
        m_safe.categories = [cat_action]

        m_flag = MovieModel(
            title="Flagged Adult Movie",
            code="ADULT1",
            publish_status="published",
            is_18_plus=True,
            genres="Drama",
        )
        m_flag.categories = [cat_action]

        m_cat = MovieModel(
            title="Category Adult Movie",
            code="ADULT2",
            publish_status="published",
            is_18_plus=False,
            genres="Erotika",
        )
        m_cat.categories = [cat_18]

        s_safe = SeriesModel(
            title="Safe Series",
            publish_status="published",
            is_18_plus=False,
        )
        s_safe.categories = [cat_action]

        s_adult = SeriesModel(
            title="Adult Series",
            publish_status="published",
            is_18_plus=True,
        )
        s_adult.categories = [cat_18]

        session.add_all([m_safe, m_flag, m_cat, s_safe, s_adult])
        await session.commit()

    async def override_db():
        async with session_factory() as s:
            yield s

    app.dependency_overrides[get_db_session] = override_db

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            res_m_filtered = await client.get("/api/v1/movies?include_adult=false")
            assert res_m_filtered.status_code == 200
            m_data = res_m_filtered.json()
            assert m_data["total"] == 1
            assert [item["code"] for item in m_data["items"]] == ["SAFE1"]

            res_m_all = await client.get("/api/v1/movies?include_adult=true")
            assert res_m_all.status_code == 200
            assert res_m_all.json()["total"] == 3

            res_s_filtered = await client.get("/api/v1/series?include_adult=false")
            assert res_s_filtered.status_code == 200
            s_data = res_s_filtered.json()
            assert s_data["total"] == 1
            assert [item["title"] for item in s_data["items"]] == ["Safe Series"]

            res_live = await client.get("/api/v1/search/live?q=Adult&include_adult=false")
            assert res_live.status_code == 200
            assert res_live.json()["total"] == 0
    finally:
        app.dependency_overrides.clear()
        await engine.dispose()
