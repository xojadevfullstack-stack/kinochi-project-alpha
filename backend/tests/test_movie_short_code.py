import pytest

from app.domain.movies.entities import Movie
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.repositories.movie_repo import MovieRepositoryImpl


@pytest.mark.asyncio
async def test_repository_assigns_sequential_short_code_and_resolves_both(db_session):
    repo = MovieRepositoryImpl(db_session)

    m1 = await repo.create(Movie(title="Birinchi Kino", code="ABC123", publish_status="published"))
    m2 = await repo.create(Movie(title="Ikkinchi Kino", code="XYZ789", publish_status="published"))
    await db_session.commit()

    assert m1.short_code is not None and m1.short_code.isdigit()
    assert int(m1.short_code) >= 1001
    assert m2.short_code == str(int(m1.short_code) + 1)
    assert m1.code == "ABC123"

    # Resolve by short_code and by legacy code
    found_short = await repo.get_by_code(m1.short_code, publish_status="published")
    found_legacy = await repo.get_by_code("abc123", publish_status="published")
    assert found_short is not None and found_short.id == m1.id
    assert found_legacy is not None and found_legacy.id == m1.id


@pytest.mark.asyncio
async def test_short_code_takes_priority_over_numeric_id_fallback(db_session):
    repo = MovieRepositoryImpl(db_session)

    m1 = await repo.create(Movie(title="Birinchi Film", code="FIRST1", publish_status="published"))
    # Insert a movie explicitly at id=1001 with its own short_code="2005"
    m_collision = MovieModel(
        id=1001,
        title="Id 1001 Film",
        code="COLL11",
        short_code="2005",
        publish_status="published",
    )
    db_session.add(m_collision)
    await db_session.commit()

    # Searching m1.short_code ("1001") MUST return m1, NOT m_collision (id=1001)
    found = await repo.get_by_code(m1.short_code, publish_status="published")
    assert found is not None
    assert found.id == m1.id

    # Searching "2005" returns m_collision
    found_2005 = await repo.get_by_code("2005", publish_status="published")
    assert found_2005 is not None
    assert found_2005.id == 1001


@pytest.mark.asyncio
async def test_movies_api_and_live_search_support_short_code(client, db_session):
    repo = MovieRepositoryImpl(db_session)
    m = await repo.create(Movie(title="Qasoskorlar: Intiho", code="QASOS1", publish_status="published"))
    await db_session.commit()

    assert m.short_code is not None and m.short_code.isdigit()

    r_short = client.get(f"/api/v1/movies/code/{m.short_code}")
    assert r_short.status_code == 200
    assert r_short.json()["code"] == "QASOS1"
    assert r_short.json()["short_code"] == m.short_code

    r_legacy = client.get("/api/v1/movies/code/QASOS1")
    assert r_legacy.status_code == 200
    assert r_legacy.json()["short_code"] == m.short_code

    r_live = client.get(f"/api/v1/search/live?q={m.short_code}")
    assert r_live.status_code == 200
    items = r_live.json()["results"]
    assert any(it["id"] == m.id and it.get("short_code") == m.short_code for it in items)
