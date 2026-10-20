import time
import json
import fnmatch
import logging
from typing import Any, Optional
from redis.exceptions import RedisError
from app.core.job_manager import job_manager

logger = logging.getLogger(__name__)

# Fallback in-memory cache with TTL (key -> (value, expire_timestamp))
_memory_cache: dict[str, tuple[Any, float]] = {}
_redis_disabled = False

try:
    from app.core.config import settings
    _redis_url = getattr(settings, "REDIS_URL", "")
    if "SIZNING_UPSTASH_PAROLINGIZ" in _redis_url or "parol" in _redis_url.lower():
        _redis_disabled = True
except Exception:
    pass

async def get_cache(key: str) -> Optional[Any]:
    """Retrieve data from Redis cache or fallback in-memory cache."""
    global _redis_disabled
    now = time.time()

    # In-memory keshni tekshirish
    if key in _memory_cache:
        val, exp = _memory_cache[key]
        if now < exp:
            return val
        else:
            _memory_cache.pop(key, None)

    if _redis_disabled:
        return None

    try:
        data = await job_manager._redis.get(key)
        if data:
            val = json.loads(data)
            _memory_cache[key] = (val, now + 60)
            return val
    except RedisError as e:
        if not _redis_disabled:
            logger.warning(f"Redis get_cache xatosi ({e}). In-memory kesh zaxirasiga o'tkazildi.")
            _redis_disabled = True
    except Exception as e:
        logger.debug(f"Cache decode error for key {key}: {e}")
    return None

async def set_cache(key: str, data: Any, ttl_seconds: int = 300) -> bool:
    """Store data in Redis cache with TTL, fallback to memory."""
    global _redis_disabled
    now = time.time()
    _memory_cache[key] = (data, now + ttl_seconds)

    if _redis_disabled:
        return True

    try:
        await job_manager._redis.setex(key, ttl_seconds, json.dumps(data))
        return True
    except RedisError as e:
        if not _redis_disabled:
            logger.warning(f"Redis set_cache xatosi ({e}). In-memory kesh zaxirasiga o'tkazildi.")
            _redis_disabled = True
    except Exception as e:
        logger.debug(f"Cache encode error for key {key}: {e}")
    return True

async def delete_cache_pattern(pattern: str) -> None:
    """Delete keys matching a specific pattern from both memory and Redis."""
    global _redis_disabled
    to_delete = [k for k in list(_memory_cache.keys()) if fnmatch.fnmatch(k, pattern)]
    for k in to_delete:
        _memory_cache.pop(k, None)

    if _redis_disabled:
        return

    try:
        if job_manager._redis:
            keys = await job_manager._redis.keys(pattern)
            if keys:
                await job_manager._redis.delete(*keys)
    except RedisError as e:
        if not _redis_disabled:
            _redis_disabled = True
    except Exception as e:
        logger.debug(f"Redis delete keys error: {e}")


def clear_memory_cache() -> None:
    """In-memory zaxira keshini to'liq tozalaydi."""
    global _memory_cache
    _memory_cache.clear()


def get_memory_cache_keys() -> list[str]:
    """In-memory kesh kalitlarini qaytaradi (testlar va audit uchun)."""
    return list(_memory_cache.keys())


async def flush_all_cache() -> None:
    """In-memory va Redis keshlarini (faqat cache:* kalitlarini) xavfsiz tozalaydi (flushdb ishlatilmaydi)."""
    clear_memory_cache()
    await delete_cache_pattern("cache:*")


async def invalidate_media_cache(media_type: str = "all") -> None:
    """
    Publish status o'zgarganda yoki media yozilganda keshni (memory + Redis) tozalaydi.
    """
    if media_type in ("movie", "movies"):
        await delete_cache_pattern("cache:movies:*")
        await delete_cache_pattern("cache:search:*")
    elif media_type in ("series", "season", "episode"):
        await delete_cache_pattern("cache:series:*")
        await delete_cache_pattern("cache:search:*")
    else:
        await delete_cache_pattern("cache:movies:*")
        await delete_cache_pattern("cache:series:*")
        await delete_cache_pattern("cache:search:*")
        await delete_cache_pattern("cache:*")
