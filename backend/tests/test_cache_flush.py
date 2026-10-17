import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.cache import (
    get_cache,
    set_cache,
    delete_cache_pattern,
    flush_all_cache,
    clear_memory_cache,
    get_memory_cache_keys,
    invalidate_media_cache,
    _memory_cache,
)
from app.api.deps import get_current_admin


@pytest.fixture(autouse=True)
def clean_memory_cache_fixture():
    """Har bir testdan oldin va keyin in-memory keshni tozalash."""
    clear_memory_cache()
    yield
    clear_memory_cache()
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_set_and_get_memory_cache_fallback():
    """Redis bo'lmaganda yoki o'chirilganda in-memory kesh to'g'ri ishlaydi."""
    with patch("app.core.cache._redis_disabled", True):
        await set_cache("test:key:1", {"foo": "bar"}, ttl_seconds=60)
        cached = await get_cache("test:key:1")
        assert cached == {"foo": "bar"}
        assert "test:key:1" in get_memory_cache_keys()


@pytest.mark.asyncio
async def test_delete_cache_pattern_clears_memory_and_redis():
    """delete_cache_pattern ham in-memory, ham Redis kalitlarini o'chiradi."""
    mock_redis = AsyncMock()
    mock_redis.keys.return_value = ["cache:movies:1", "cache:movies:2"]

    with patch("app.core.job_manager.job_manager._redis", mock_redis), \
         patch("app.core.cache._redis_disabled", False):

        # Memory keshga yozamiz
        await set_cache("cache:movies:1", "data1", 300)
        await set_cache("cache:movies:2", "data2", 300)
        await set_cache("cache:series:1", "data3", 300)

        assert len(get_memory_cache_keys()) == 3

        # Faqat movies keshini o'chiramiz
        await delete_cache_pattern("cache:movies:*")

        # Memory keshda faqat series qolishi kerak
        assert "cache:movies:1" not in _memory_cache
        assert "cache:movies:2" not in _memory_cache
        assert "cache:series:1" in _memory_cache

        # Redis delete chaqirilgan bo'lishi kerak
        mock_redis.keys.assert_called_with("cache:movies:*")
        mock_redis.delete.assert_called_with("cache:movies:1", "cache:movies:2")


@pytest.mark.asyncio
async def test_flush_all_cache_clears_both_memory_and_redis():
    """flush_all_cache() ham in-memory keshni, ham Redis flushdb() ni to'liq tozalaydi."""
    mock_redis = AsyncMock()

    with patch("app.core.job_manager.job_manager._redis", mock_redis), \
         patch("app.core.cache._redis_disabled", False):

        await set_cache("key1", "val1", 300)
        await set_cache("key2", "val2", 300)
        assert len(get_memory_cache_keys()) == 2

        await flush_all_cache()

        # In-memory butunlay bo'sh bo'lishi shart
        assert len(get_memory_cache_keys()) == 0
        # Redis flushdb() chaqirilgan bo'lishi shart
        mock_redis.flushdb.assert_called_once()


@pytest.mark.asyncio
async def test_invalidate_media_cache_on_publish():
    """invalidate_media_cache movies yoki series uchun mos kesh kalitlarini tozalaydi."""
    mock_redis = AsyncMock()
    mock_redis.keys.return_value = []

    with patch("app.core.job_manager.job_manager._redis", mock_redis), \
         patch("app.core.cache._redis_disabled", False):

        await set_cache("cache:movies:list", "list_data", 300)
        await set_cache("cache:search:live", "search_data", 300)
        await set_cache("cache:series:list", "series_data", 300)

        # Movies uchun invalidatsiya
        await invalidate_media_cache("movie")
        assert "cache:movies:list" not in _memory_cache
        assert "cache:search:live" not in _memory_cache
        assert "cache:series:list" in _memory_cache

        # Series uchun invalidatsiya
        await invalidate_media_cache("series")
        assert "cache:series:list" not in _memory_cache


@pytest.mark.asyncio
async def test_admin_cache_flush_endpoint_unauthorized():
    """Admin tokeni bo'lmasa, POST /api/v1/admin/cache/flush 401 qaytaradi."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/v1/admin/cache/flush")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_cache_flush_endpoint_success():
    """Admin huquqi bilan POST /api/v1/admin/cache/flush chaqirilganda 200 qaytaradi va keshni tozalaydi."""
    fake_admin = MagicMock()
    fake_admin.id = 1
    fake_admin.role = "admin"

    app.dependency_overrides[get_current_admin] = lambda: fake_admin

    mock_redis = AsyncMock()
    with patch("app.core.job_manager.job_manager._redis", mock_redis), \
         patch("app.core.cache._redis_disabled", False):

        await set_cache("dummy:key", "dummy:val", 300)
        assert len(get_memory_cache_keys()) == 1

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/api/v1/admin/cache/flush")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        # In-memory kesh tozalangan bo'lishi shart
        assert len(get_memory_cache_keys()) == 0
        # Redis flushdb chaqirilgan bo'lishi shart
        mock_redis.flushdb.assert_called_once()
