import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_db_session
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.models.category import CategoryModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel
from app.infrastructure.db.session import Base


@pytest.fixture
async def series_perf_db():
    """Lokal test muhitida seriallar bilan to'ldirilgan SQLite in-memory DB yaratadi."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    # 1. Seed ma'lumotlarini kiritish (masalan 10 ta serial, har birida 3 fasl, 5 qism, 2 tarjima)
    async with session_factory() as session:
        cat = CategoryModel(id=1, name="Drama", slug="drama")
        session.add(cat)
        await session.flush()

        for s_idx in range(1, 11):
            ser = SeriesModel(
                id=s_idx,
                title=f"Test Series {s_idx}",
                description=f"Description for series {s_idx}",
                release_year=2020 + s_idx,
                publish_status="published",
                status="ongoing"
            )
            ser.categories.append(cat)
            session.add(ser)
            await session.flush()

            for sn_num in range(1, 4):
                season = SeasonModel(
                    series_id=ser.id,
                    season_number=sn_num,
                    title=f"Season {sn_num}",
                    status="completed"
                )
                session.add(season)
                await session.flush()

                for ep_num in range(1, 6):
                    ep = EpisodeModel(
                        season_id=season.id,
                        episode_number=ep_num,
                        code=f"s{ser.id}_sn{sn_num}_e{ep_num}",
                        display_code=f"s{ser.id}e{ep_num}",
                        title=f"Episode {ep_num}"
                    )
                    session.add(ep)
                    await session.flush()

                    tr = EpisodeTranslationModel(
                        episode_id=ep.id,
                        language="uz",
                        telegram_file_id=f"file_id_{ep.id}"
                    )
                    session.add(tr)
        await session.commit()

    yield engine, session_factory
    await engine.dispose()


@pytest.mark.asyncio
async def test_series_list_and_search_query_count_and_no_seasons(series_perf_db):
    """
    C0.4: Seriallar ro'yxati va qidiruvida:
    1. SQL so'rovlar soni <= 3 (seasons/episodes/translations yuklanmaydi).
    2. Javob elementlarida 'seasons' kaliti umuman yo'q.
    3. Detail endpointda esa 'seasons' to'liq saqlangan (regression tekshiruvi).
    """
    engine, session_factory = series_perf_db

    async def override_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db_session] = override_db

    client = TestClient(app)
    try:
        # A) Ro'yxat so'rovi (GET /api/v1/series)
        queries = []

        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            queries.append(statement)

        event.listen(engine.sync_engine, "before_cursor_execute", before_cursor_execute)

        resp = client.get("/api/v1/series?limit=5")
        assert resp.status_code == 200, resp.text
        data = resp.json()

        # 1. SQL so'rovlar soni tekshiruvi (count + series list + categories/pages eager loads <= 3)
        assert len(queries) <= 3, f"Kutilgan <= 3 ta SQL so'rov, ammo bajarildi {len(queries)}: {queries}"

        # 2. Javobda seasons kaliti yo'qligi
        assert len(data["items"]) == 5
        for item in data["items"]:
            assert "seasons" not in item, f"Ro'yxat javobida 'seasons' kaliti bo'lmasligi kerak: {item.keys()}"

        # B) Qidiruv so'rovi (GET /api/v1/series/search)
        queries.clear()
        search_resp = client.get("/api/v1/series/search?q=Series")
        assert search_resp.status_code == 200, search_resp.text
        search_data = search_resp.json()

        assert len(queries) <= 3, f"Qidiruvda kutilgan <= 3 ta SQL so'rov, bajarildi {len(queries)}"
        assert len(search_data["items"]) > 0
        for item in search_data["items"]:
            assert "seasons" not in item, f"Qidiruv javobida 'seasons' kaliti bo'lmasligi kerak: {item.keys()}"

        # C) Regression: Detail so'rovi (GET /api/v1/series/{id})
        detail_resp = client.get("/api/v1/series/1")
        assert detail_resp.status_code == 200, detail_resp.text
        detail_data = detail_resp.json()

        # Detailda seasons bo'lishi shart
        assert "seasons" in detail_data, "Detail endpointda 'seasons' bo'lishi shart!"
        assert len(detail_data["seasons"]) == 3
        assert len(detail_data["seasons"][0]["episodes"]) == 5
        assert len(detail_data["seasons"][0]["episodes"][0]["translations"]) == 1

    finally:
        app.dependency_overrides.pop(get_db_session, None)
        event.remove(engine.sync_engine, "before_cursor_execute", before_cursor_execute)
