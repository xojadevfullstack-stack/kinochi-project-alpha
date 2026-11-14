import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.cache import invalidate_media_cache, set_cache, get_cache, _memory_cache, clear_memory_cache

@pytest.fixture(autouse=True)
def clean_cache():
    clear_memory_cache()
    yield
    clear_memory_cache()

@pytest.mark.asyncio
async def test_invalidate_media_cache_clears_episode_cache():
    """Assert that invalidating series media cache also clears cache:episode:*."""
    mock_redis = AsyncMock()
    mock_redis.keys.return_value = []

    with patch("app.core.job_manager.job_manager._redis", mock_redis), \
         patch("app.core.cache._redis_disabled", False):

        await set_cache("cache:series:detail:123", {"title": "Test Series"}, 300)
        await set_cache("cache:episode:detail:ep_code_1", {"title": "Episode 1"}, 300)

        assert "cache:series:detail:123" in _memory_cache
        assert "cache:episode:detail:ep_code_1" in _memory_cache

        # Invalidate series
        await invalidate_media_cache("series")

        # Both series and episode caches must be purged
        assert "cache:series:detail:123" not in _memory_cache
        assert "cache:episode:detail:ep_code_1" not in _memory_cache
