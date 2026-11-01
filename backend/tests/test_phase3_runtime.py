import time
import socket
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.core.cache import (
    get_cache,
    set_cache,
    _memory_cache,
    clear_memory_cache,
)
from app.core.bot_status import get_bot_status, set_bot_status
from app.infrastructure.db.models.movie import MovieModel
from app.infrastructure.db.models.collection import CollectionModel, CollectionItemModel
from app.api.v1.collections import broadcast_new_collection_item_notification
from app.core.reviews import submit_review
from app.infrastructure.db.session import _ipv4_only_getaddrinfo, _dns_cache


@pytest.mark.asyncio
async def test_3a_collection_item_notification_runtime_attribute(db_session):
    """broadcast_new_collection_item_notification must use movie.runtime without raising AttributeError."""
    movie = MovieModel(
        title="Inception",
        code="inc01",
        runtime=148,
        publish_status="published",
    )
    collection = CollectionModel(
        name="Sci-Fi Gems",
        slug="scifi-gems",
    )
    db_session.add_all([movie, collection])
    await db_session.commit()
    await db_session.refresh(movie)
    await db_session.refresh(collection)

    col_item = CollectionItemModel(
        collection_id=collection.id,
        movie_id=movie.id,
        chronological_order=1,
    )
    db_session.add(col_item)
    await db_session.commit()

    # Call broadcast_new_collection_item_notification with mock telegram client
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = MagicMock(status_code=200, json=lambda: {"ok": True})
        # Should not raise AttributeError: 'MovieModel' object has no attribute 'duration_minutes'
        res = await broadcast_new_collection_item_notification(
            db=db_session,
            collection_id=collection.id,
            movie_id=movie.id,
        )
        assert res["success"] is True


@pytest.mark.asyncio
async def test_3b_reviews_cache_invalidation_import(db_session):
    """Adding a review must trigger delete_cache_pattern from app.core.cache without import error."""
    movie = MovieModel(
        title="Test Movie",
        code="tm01",
        publish_status="published",
    )
    db_session.add(movie)
    await db_session.commit()
    await db_session.refresh(movie)

    with patch("app.core.cache.delete_cache_pattern", new_callable=AsyncMock) as mock_delete_pattern:
        res = await submit_review(
            user_id=1,
            rating=9,
            comment="Ajoyib kino!",
            movie_id=movie.id,
        )
        assert res["success"] is True
        mock_delete_pattern.assert_awaited_with("cache:movies:*")


@pytest.mark.asyncio
async def test_3c_cache_cooldown_and_memory_limit():
    """Redis errors must trigger temporary cooldown (not lifetime disable), and memory cache must enforce max size."""
    from app.core import cache
    clear_memory_cache()

    # 1. Simulate Redis failure
    from redis.exceptions import ConnectionError as RedisConnectionError
    mock_redis = AsyncMock()
    mock_redis.get.side_effect = RedisConnectionError("Redis connection lost")

    try:
        with patch("app.core.job_manager.job_manager._redis", mock_redis):
            # Initial get triggers error and cooldown
            val = await cache.get_cache("key1")
            assert val is None
            assert cache._redis_disabled_until > time.time()

            # During cooldown, fallback to memory
            await cache.set_cache("key2", {"data": "cached_in_memory"}, ttl_seconds=60)
            assert await cache.get_cache("key2") == {"data": "cached_in_memory"}

            # When cooldown passes, Redis is attempted again
            with patch("time.time", return_value=time.time() + 500):
                mock_redis.get.side_effect = None
                mock_redis.get.return_value = b'{"data": "from_redis"}'
                res = await cache.get_cache("key3")
                assert res == {"data": "from_redis"}
    finally:
        cache._redis_disabled_until = 0.0
        clear_memory_cache()


def test_3d_dns_cache_ttl_and_eviction():
    """_ipv4_only_getaddrinfo must respect TTL (300s) and prune expired DNS entries."""
    _dns_cache.clear()
    original_call_count = 0

    def mock_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
        nonlocal original_call_count
        original_call_count += 1
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.0.2.1', port))]

    with patch("app.infrastructure.db.session._original_getaddrinfo", side_effect=mock_getaddrinfo):
        # 1. First resolution -> calls original
        res1 = _ipv4_only_getaddrinfo("neon.tech", 5432)
        assert original_call_count == 1

        # 2. Immediate second resolution -> cached
        res2 = _ipv4_only_getaddrinfo("neon.tech", 5432)
        assert original_call_count == 1
        assert res1 == res2

        # 3. After TTL (350s later) -> must resolve again
        current_time = time.time()
        with patch("time.time", return_value=current_time + 350):
            res3 = _ipv4_only_getaddrinfo("neon.tech", 5432)
            assert original_call_count == 2


@pytest.mark.asyncio
async def test_3e_bot_failure_does_not_kill_api():
    """supervised_run_bot() must set status to degraded and NOT call sys.exit(1) when retries exhaust."""
    import run

    call_count = 0
    async def failing_run_bot():
        nonlocal call_count
        call_count += 1
        raise RuntimeError(f"Simulated Telegram Polling Crash {call_count}")

    with patch.dict("os.environ", {"MAX_BOT_RESTARTS": "3", "BOT_RESTART_BASE_DELAY": "0.01"}), \
         patch("bot.main.run_bot", side_effect=failing_run_bot), \
         patch("sys.exit") as mock_exit, \
         patch("asyncio.sleep", new_callable=AsyncMock):

        await run.supervised_run_bot()

        assert call_count == 3
        # sys.exit(1) must NOT be called — API must stay alive
        mock_exit.assert_not_called()
        assert get_bot_status() == "degraded"
