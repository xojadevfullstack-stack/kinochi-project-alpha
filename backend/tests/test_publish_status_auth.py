"""
Tests for publish_status authentication on movie and series endpoints:
1. Detail endpoints:
   - GET /api/v1/movies/{id}
   - GET /api/v1/series/{id}
2. List & search endpoints:
   - GET /api/v1/movies
   - GET /api/v1/movies/search
   - GET /api/v1/series
   - GET /api/v1/series/search

Verifies:
- Unauthenticated ?publish_status=all|pending|hidden -> 403 Forbidden
- Unauthenticated default (no param) -> 200 OK (only published content)
- Non-admin user token with non-published status -> 403 Forbidden
- Admin token with ?publish_status=all|pending -> 200 OK
"""
import pytest
from unittest.mock import AsyncMock, MagicMock
from httpx import AsyncClient, ASGITransport
from datetime import datetime

from app.main import app
from app.api.deps import get_movie_service, get_series_service, get_db_session
from app.domain.movies.entities import Movie
from app.domain.series.entities import Series
from app.infrastructure.db.models.admin_user import AdminUserModel
from app.infrastructure.security.jwt_handler import create_access_token


@pytest.fixture
def published_movie():
    return Movie(
        id=1,
        title="Published Movie",
        code="pub12345",
        publish_status="published",
        release_year=2024,
    )


@pytest.fixture
def pending_movie():
    return Movie(
        id=2,
        title="Pending Movie",
        code="pen12345",
        publish_status="pending",
        release_year=2024,
    )


@pytest.fixture
def published_series():
    return Series(
        id=1,
        title="Published Series",
        code="s_pub1",
        publish_status="published",
        release_year=2024,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def pending_series():
    return Series(
        id=2,
        title="Pending Series",
        code="s_pen2",
        publish_status="pending",
        release_year=2024,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def admin_token():
    return create_access_token(
        subject="1",
        extra={"email": "admin@kinochi.uz", "role": "admin"}
    )


@pytest.fixture
def user_token():
    return create_access_token(
        subject="99",
        extra={"email": "user@kinochi.uz", "role": "user"}
    )


@pytest.fixture
def mock_admin_db():
    mock_db = AsyncMock()
    admin_model = AdminUserModel(
        id=1,
        email="admin@kinochi.uz",
        role="admin",
        is_active=True,
    )
    mock_res = MagicMock()
    mock_res.scalar_one_or_none.return_value = admin_model
    mock_db.execute.return_value = mock_res
    return mock_db


@pytest.mark.asyncio
async def test_movie_detail_publish_status_auth(
    published_movie,
    pending_movie,
    admin_token,
    user_token,
    mock_admin_db,
):
    mock_movie_service = AsyncMock()

    async def fake_get_movie(movie_id: int, publish_status: str | None = None):
        if movie_id == 1:
            if publish_status is None or publish_status == "published":
                return published_movie
            return None
        elif movie_id == 2:
            if publish_status is None or publish_status == "pending":
                return pending_movie
            return None
        return None

    mock_movie_service.get_movie.side_effect = fake_get_movie

    app.dependency_overrides[get_movie_service] = lambda: mock_movie_service
    app.dependency_overrides[get_db_session] = lambda: mock_admin_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 1. Unauthenticated default -> 200 for published movie
            res = await ac.get("/api/v1/movies/1")
            assert res.status_code == 200
            assert res.json()["id"] == 1
            assert res.json()["publish_status"] == "published"

            # 2. Unauthenticated default -> 404 for pending movie (hidden from public)
            res = await ac.get("/api/v1/movies/2")
            assert res.status_code == 404

            # 3. Unauthenticated ?publish_status=published -> 200 for published movie
            res = await ac.get("/api/v1/movies/1?publish_status=published")
            assert res.status_code == 200

            # 4. Unauthenticated non-published statuses -> 403 Forbidden
            for st in ("all", "pending", "hidden"):
                res = await ac.get(f"/api/v1/movies/1?publish_status={st}")
                assert res.status_code == 403, f"Expected 403 for publish_status={st}"

            # 5. Non-admin user token with ?publish_status=all -> 403 Forbidden
            res = await ac.get(
                "/api/v1/movies/2?publish_status=all",
                headers={"Authorization": f"Bearer {user_token}"}
            )
            assert res.status_code == 403

            # 6. Admin token with ?publish_status=all -> 200 OK (access to pending movie)
            res = await ac.get(
                "/api/v1/movies/2?publish_status=all",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert res.status_code == 200
            assert res.json()["id"] == 2
            assert res.json()["publish_status"] == "pending"

            # 7. Admin token with ?publish_status=pending -> 200 OK
            res = await ac.get(
                "/api/v1/movies/2?publish_status=pending",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert res.status_code == 200
            assert res.json()["id"] == 2
    finally:
        app.dependency_overrides.pop(get_movie_service, None)
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_series_detail_publish_status_auth(
    published_series,
    pending_series,
    admin_token,
    user_token,
    mock_admin_db,
):
    mock_series_service = AsyncMock()

    async def fake_get_series(series_id: int, publish_status: str | None = None):
        if series_id == 1:
            if publish_status is None or publish_status == "published":
                return published_series
            return None
        elif series_id == 2:
            if publish_status is None or publish_status == "pending":
                return pending_series
            return None
        return None

    mock_series_service.get_series_by_id.side_effect = fake_get_series

    app.dependency_overrides[get_series_service] = lambda: mock_series_service
    app.dependency_overrides[get_db_session] = lambda: mock_admin_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 1. Unauthenticated default -> 200 for published series
            res = await ac.get("/api/v1/series/1")
            assert res.status_code == 200
            assert res.json()["id"] == 1
            assert res.json()["publish_status"] == "published"

            # 2. Unauthenticated default -> 404 for pending series (hidden from public)
            res = await ac.get("/api/v1/series/2")
            assert res.status_code == 404

            # 3. Unauthenticated ?publish_status=published -> 200 for published series
            res = await ac.get("/api/v1/series/1?publish_status=published")
            assert res.status_code == 200

            # 4. Unauthenticated non-published statuses -> 403 Forbidden
            for st in ("all", "pending", "hidden"):
                res = await ac.get(f"/api/v1/series/1?publish_status={st}")
                assert res.status_code == 403, f"Expected 403 for publish_status={st}"

            # 5. Non-admin user token with ?publish_status=all -> 403 Forbidden
            res = await ac.get(
                "/api/v1/series/2?publish_status=all",
                headers={"Authorization": f"Bearer {user_token}"}
            )
            assert res.status_code == 403

            # 6. Admin token with ?publish_status=all -> 200 OK (access to pending series)
            res = await ac.get(
                "/api/v1/series/2?publish_status=all",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert res.status_code == 200
            assert res.json()["id"] == 2
            assert res.json()["publish_status"] == "pending"

            # 7. Admin token with ?publish_status=pending -> 200 OK
            res = await ac.get(
                "/api/v1/series/2?publish_status=pending",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert res.status_code == 200
            assert res.json()["id"] == 2
    finally:
        app.dependency_overrides.pop(get_series_service, None)
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_movies_list_and_search_publish_status_auth(
    published_movie,
    pending_movie,
    admin_token,
    user_token,
    mock_admin_db,
):
    mock_movie_service = AsyncMock()
    mock_movie_service.list_movies.return_value = ([published_movie], 1)
    mock_movie_service.search_movies.return_value = ([published_movie], 1)

    app.dependency_overrides[get_movie_service] = lambda: mock_movie_service
    app.dependency_overrides[get_db_session] = lambda: mock_admin_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            for endpoint in ("/api/v1/movies", "/api/v1/movies/search?q=test"):
                sep = "&" if "?" in endpoint else "?"

                # 1. Unauthenticated default -> 200
                res = await ac.get(endpoint)
                assert res.status_code == 200

                # 2. Unauthenticated ?publish_status=published -> 200
                res = await ac.get(f"{endpoint}{sep}publish_status=published")
                assert res.status_code == 200

                # 3. Unauthenticated all/pending/hidden -> 403 Forbidden
                for st in ("all", "pending", "hidden"):
                    res = await ac.get(f"{endpoint}{sep}publish_status={st}")
                    assert res.status_code == 403, f"{endpoint} expected 403 for {st}"

                # 4. User token with publish_status=all -> 403 Forbidden
                res = await ac.get(
                    f"{endpoint}{sep}publish_status=all",
                    headers={"Authorization": f"Bearer {user_token}"}
                )
                assert res.status_code == 403

                # 5. Admin token with publish_status=all -> 200 OK
                res = await ac.get(
                    f"{endpoint}{sep}publish_status=all",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert res.status_code == 200
    finally:
        app.dependency_overrides.pop(get_movie_service, None)
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_series_list_and_search_publish_status_auth(
    published_series,
    pending_series,
    admin_token,
    user_token,
    mock_admin_db,
):
    mock_series_service = AsyncMock()
    mock_series_service.get_all_series.return_value = ([published_series], 1)
    mock_series_service.search_series.return_value = ([published_series], 1)

    app.dependency_overrides[get_series_service] = lambda: mock_series_service
    app.dependency_overrides[get_db_session] = lambda: mock_admin_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            for endpoint in ("/api/v1/series", "/api/v1/series/search?q=test"):
                sep = "&" if "?" in endpoint else "?"

                # 1. Unauthenticated default -> 200
                res = await ac.get(endpoint)
                assert res.status_code == 200

                # 2. Unauthenticated ?publish_status=published -> 200
                res = await ac.get(f"{endpoint}{sep}publish_status=published")
                assert res.status_code == 200

                # 3. Unauthenticated all/pending/hidden -> 403 Forbidden
                for st in ("all", "pending", "hidden"):
                    res = await ac.get(f"{endpoint}{sep}publish_status={st}")
                    assert res.status_code == 403, f"{endpoint} expected 403 for {st}"

                # 4. User token with publish_status=all -> 403 Forbidden
                res = await ac.get(
                    f"{endpoint}{sep}publish_status=all",
                    headers={"Authorization": f"Bearer {user_token}"}
                )
                assert res.status_code == 403

                # 5. Admin token with publish_status=all -> 200 OK
                res = await ac.get(
                    f"{endpoint}{sep}publish_status=all",
                    headers={"Authorization": f"Bearer {admin_token}"}
                )
                assert res.status_code == 200
    finally:
        app.dependency_overrides.pop(get_series_service, None)
        app.dependency_overrides.pop(get_db_session, None)
