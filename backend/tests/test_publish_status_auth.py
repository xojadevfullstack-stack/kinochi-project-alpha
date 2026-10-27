"""
Parametrized tests for publish_status authentication across 6 endpoints:
1. GET /api/v1/movies/{id}
2. GET /api/v1/series/{id}
3. GET /api/v1/movies
4. GET /api/v1/movies/search?q=test
5. GET /api/v1/series
6. GET /api/v1/series/search?q=test

Test categories:
(a) Unauthenticated with non-published status (all, pending, hidden, foo) -> 401 Unauthorized
(b) Invalid / expired token with all -> 401 Unauthorized
(c) Normal user token with all or pending -> 403 Forbidden
(d) Admin token with all -> 200 OK (includes unpublished content, total=2)
(e) Admin token with pending -> 200 OK (only pending content, total=1)
(f) Unauthenticated default or published -> 200 OK (only published content, total=1)
(g) Cache isolation test -> Admin 'all' cache does not leak to public default
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
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


@pytest.fixture(autouse=True)
def setup_services(published_movie, pending_movie, published_series, pending_series, mock_admin_db):
    # Mock Movie Service
    mock_m_service = AsyncMock()

    async def fake_get_movie(movie_id: int, publish_status: str | None = None):
        if movie_id == 1:
            return published_movie if publish_status in (None, "published") else None
        elif movie_id == 2:
            return pending_movie if publish_status in (None, "pending") else None
        return None

    async def fake_list_movies(**kwargs):
        ps = kwargs.get("publish_status")
        if ps == "published":
            return ([published_movie], 1)
        elif ps == "pending":
            return ([pending_movie], 1)
        elif ps is None:
            return ([published_movie, pending_movie], 2)
        return ([], 0)

    async def fake_search_movies(**kwargs):
        ps = kwargs.get("publish_status")
        if ps == "published":
            return ([published_movie], 1)
        elif ps == "pending":
            return ([pending_movie], 1)
        elif ps is None:
            return ([published_movie, pending_movie], 2)
        return ([], 0)

    mock_m_service.get_movie.side_effect = fake_get_movie
    mock_m_service.list_movies.side_effect = fake_list_movies
    mock_m_service.search_movies.side_effect = fake_search_movies

    # Mock Series Service
    mock_s_service = AsyncMock()

    async def fake_get_series(series_id: int, publish_status: str | None = None):
        if series_id == 1:
            return published_series if publish_status in (None, "published") else None
        elif series_id == 2:
            return pending_series if publish_status in (None, "pending") else None
        return None

    async def fake_get_all_series(**kwargs):
        ps = kwargs.get("publish_status")
        if ps == "published":
            return ([published_series], 1)
        elif ps == "pending":
            return ([pending_series], 1)
        elif ps is None:
            return ([published_series, pending_series], 2)
        return ([], 0)

    async def fake_search_series(**kwargs):
        ps = kwargs.get("publish_status")
        if ps == "published":
            return ([published_series], 1)
        elif ps == "pending":
            return ([pending_series], 1)
        elif ps is None:
            return ([published_series, pending_series], 2)
        return ([], 0)

    mock_s_service.get_series_by_id.side_effect = fake_get_series
    mock_s_service.get_all_series.side_effect = fake_get_all_series
    mock_s_service.search_series.side_effect = fake_search_series

    app.dependency_overrides[get_movie_service] = lambda: mock_m_service
    app.dependency_overrides[get_series_service] = lambda: mock_s_service
    app.dependency_overrides[get_db_session] = lambda: mock_admin_db

    yield

    app.dependency_overrides.pop(get_movie_service, None)
    app.dependency_overrides.pop(get_series_service, None)
    app.dependency_overrides.pop(get_db_session, None)


ALL_ENDPOINTS = [
    "/api/v1/movies/1",
    "/api/v1/series/1",
    "/api/v1/movies",
    "/api/v1/movies/search?q=test",
    "/api/v1/series",
    "/api/v1/series/search?q=test",
]


# (a) Unauthenticated with non-published status -> 401 Unauthorized
@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", ALL_ENDPOINTS)
@pytest.mark.parametrize("status_val", ["all", "pending", "hidden", "foo"])
async def test_unauthenticated_non_published_returns_401(endpoint, status_val):
    sep = "&" if "?" in endpoint else "?"
    url = f"{endpoint}{sep}publish_status={status_val}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(url)
        assert res.status_code == 401
        assert "Autentifikatsiya talab qilinadi" in res.json().get("detail", "")


# (b) Invalid / expired token with all -> 401 Unauthorized
@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", ALL_ENDPOINTS)
async def test_invalid_token_returns_401(endpoint):
    sep = "&" if "?" in endpoint else "?"
    url = f"{endpoint}{sep}publish_status=all"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(url, headers={"Authorization": "Bearer invalid_expired_jwt_token"})
        assert res.status_code == 401


# (c) Normal user token with non-published status -> 403 Forbidden
@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", ALL_ENDPOINTS)
@pytest.mark.parametrize("status_val", ["all", "pending"])
async def test_normal_user_token_returns_403(endpoint, status_val, user_token):
    sep = "&" if "?" in endpoint else "?"
    url = f"{endpoint}{sep}publish_status={status_val}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(url, headers={"Authorization": f"Bearer {user_token}"})
        assert res.status_code == 403
        assert "admin" in res.json().get("detail", "").lower()


# (d) Admin token with publish_status=all -> 200 OK (unpublished content included)
@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", ALL_ENDPOINTS)
async def test_admin_token_with_all_returns_200(endpoint, admin_token):
    # For detail endpoints, check access to pending item (id=2)
    test_url = endpoint.replace("/1", "/2") if "/1" in endpoint else endpoint
    sep = "&" if "?" in test_url else "?"
    url = f"{test_url}{sep}publish_status=all"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(url, headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        data = res.json()
        if "items" in data:
            assert data["total"] == 2
            assert len(data["items"]) == 2
        else:
            assert data["id"] == 2
            assert data["publish_status"] == "pending"


# (e) Admin token with publish_status=pending -> 200 OK (only pending content)
@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", ALL_ENDPOINTS)
async def test_admin_token_with_pending_returns_200(endpoint, admin_token):
    test_url = endpoint.replace("/1", "/2") if "/1" in endpoint else endpoint
    sep = "&" if "?" in test_url else "?"
    url = f"{test_url}{sep}publish_status=pending"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(url, headers={"Authorization": f"Bearer {admin_token}"})
        assert res.status_code == 200
        data = res.json()
        if "items" in data:
            assert data["total"] == 1
            assert data["items"][0]["publish_status"] == "pending"
        else:
            assert data["id"] == 2
            assert data["publish_status"] == "pending"


# (f) Unauthenticated default or published -> 200 OK (only published content)
@pytest.mark.asyncio
@pytest.mark.parametrize("endpoint", ALL_ENDPOINTS)
@pytest.mark.parametrize("query_param", ["", "publish_status=published"])
async def test_public_default_and_published_returns_200(endpoint, query_param):
    sep = "&" if "?" in endpoint else "?"
    url = f"{endpoint}{sep}{query_param}" if query_param else endpoint
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(url)
        assert res.status_code == 200
        data = res.json()
        if "items" in data:
            assert data["total"] == 1
            assert data["items"][0]["publish_status"] == "published"
        else:
            assert data["id"] == 1
            assert data["publish_status"] == "published"


# (f2) Unauthenticated default for pending item -> 404 Not Found (hidden from public)
@pytest.mark.asyncio
@pytest.mark.parametrize("detail_endpoint", ["/api/v1/movies/2", "/api/v1/series/2"])
@pytest.mark.parametrize("query_param", ["", "?publish_status=published"])
async def test_public_pending_item_hidden_returns_404(detail_endpoint, query_param):
    url = f"{detail_endpoint}{query_param}"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        res = await ac.get(url)
        assert res.status_code == 404


# (g) Cache isolation test: Admin 'all' query must NOT leak unpublished items to public
@pytest.mark.asyncio
@pytest.mark.parametrize("media_type", ["movies", "series"])
async def test_cache_isolation_admin_all_does_not_leak_to_public(media_type, admin_token):
    cache_store = {}

    async def fake_get_cache(key):
        return cache_store.get(key)

    async def fake_set_cache(key, val, ttl=300):
        cache_store[key] = val

    module_name = f"app.api.v1.{media_type}"
    with patch(f"{module_name}.get_cache", side_effect=fake_get_cache), \
         patch(f"{module_name}.set_cache", side_effect=fake_set_cache):

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            # 1. Admin requests all -> populates cache with target_status=None
            admin_res = await ac.get(
                f"/api/v1/{media_type}?publish_status=all",
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert admin_res.status_code == 200
            assert admin_res.json()["total"] == 2
            assert len(admin_res.json()["items"]) == 2

            # Verify admin cache key contains :None
            admin_cache_keys = [k for k in cache_store.keys() if ":None" in k]
            assert len(admin_cache_keys) > 0, f"Expected cache key containing ':None', got {list(cache_store.keys())}"

            # 2. Public unauthenticated user requests default (no params)
            public_res = await ac.get(f"/api/v1/{media_type}")
            assert public_res.status_code == 200
            public_data = public_res.json()

            # Must contain ONLY published items (total=1)
            assert public_data["total"] == 1
            assert len(public_data["items"]) == 1
            assert public_data["items"][0]["publish_status"] == "published"

            # Verify public cache key contains :published and is isolated from admin key
            public_cache_keys = [k for k in cache_store.keys() if ":published" in k]
            assert len(public_cache_keys) > 0, f"Expected cache key containing ':published', got {list(cache_store.keys())}"
            assert admin_cache_keys[0] != public_cache_keys[0]
