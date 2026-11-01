import time
import json
import fnmatch
import logging
from typing import Any, Optional
from redis.exceptions import RedisError
from app.core.job_manager import job_manager
from app.core.config import settings

logger = logging.getLogger(__name__)

# Fallback in-memory cache with TTL (key -> (value, expire_timestamp))
_memory_cache: dict[str, tuple[Any, float]] = {}
_redis_disabled = False
_redis_disabled_until: float = 0.0

try:
    _redis_url = getattr(settings, "REDIS_URL", "")
    if "SIZNING_UPSTASH_PAROLINGIZ" in _redis_url or "parol" in _redis_url.lower():
        _redis_disabled = True
except Exception:
    pass


def is_redis_available() -> bool:
    """Returns True if Redis is not permanently disabled and not currently in temporary error cooldown."""
    global _redis_disabled, _redis_disabled_until
    if _redis_disabled:
        return False
    if time.time() < _redis_disabled_until:
        return False
    return True


def _trigger_redis_cooldown(err: Exception) -> None:
    """Sets a temporary cooldown after a Redis error instead of permanently disabling it."""
    global _redis_disabled_until
    cooldown = float(getattr(settings, "REDIS_COOLDOWN_SECONDS", 120))
    _redis_disabled_until = time.time() + cooldown
    logger.warning("Redis xatosi (%s). In-memory fallback va %.0fs cooldown ga o'tkazildi.", err, cooldown)


def _prune_memory_cache(max_size: int | None = None) -> None:
    """Prunes expired keys and enforces maximum size limit via FIFO eviction."""
    if max_size is None:
        max_size = int(getattr(settings, "MEMORY_CACHE_MAX_SIZE", 1000))
    now = time.time()
    # 1. Tozalash: muddati o'tganlar
    expired = [k for k, (_, exp) in _memory_cache.items() if now >= exp]
    for k in expired:
        _memory_cache.pop(k, None)
    # 2. Tozalash: hajmdan oshgan qismini FIFO bo'yicha chiqarish
    while len(_memory_cache) >= max_size:
        oldest_key = next(iter(_memory_cache))
        _memory_cache.pop(oldest_key, None)


async def get_cache(key: str) -> Optional[Any]:
    """Retrieve data from Redis cache or fallback in-memory cache."""
    now = time.time()

    # In-memory keshni tekshirish
    if key in _memory_cache:
        val, exp = _memory_cache[key]
        if now < exp:
            return val
        else:
            _memory_cache.pop(key, None)

    if not is_redis_available():
        return None

    try:
        data = await job_manager._redis.get(key)
        if data:
            val = json.loads(data)
            _prune_memory_cache()
            _memory_cache[key] = (val, now + 60)
            return val
    except RedisError as e:
        _trigger_redis_cooldown(e)
    except Exception as e:
        logger.debug("Cache decode error for key %s: %s", key, e)
    return None


async def set_cache(key: str, data: Any, ttl_seconds: int = 300) -> bool:
    """Store data in Redis cache with TTL, fallback to memory."""
    now = time.time()
    _prune_memory_cache()
    _memory_cache[key] = (data, now + ttl_seconds)

    if not is_redis_available():
        return True

    try:
        await job_manager._redis.setex(key, ttl_seconds, json.dumps(data))
        return True
    except RedisError as e:
        _trigger_redis_cooldown(e)
    except Exception as e:
        logger.debug("Cache encode error for key %s: %s", key, e)
    return True


async def delete_cache_pattern(pattern: str) -> None:
    """Delete keys matching a specific pattern from both memory and Redis."""
    to_delete = [k for k in list(_memory_cache.keys()) if fnmatch.fnmatch(k, pattern)]
    for k in to_delete:
        _memory_cache.pop(k, None)

    if not is_redis_available():
        return

    try:
        if job_manager._redis:
            keys = await job_manager._redis.keys(pattern)
            if keys:
                await job_manager._redis.delete(*keys)
    except RedisError as e:
        _trigger_redis_cooldown(e)
    except Exception as e:
        logger.debug("Redis delete keys error: %s", e)


def clear_memory_cache() -> None:
    """In-memory zaxira keshini to'liq tozalaydi."""
    global _memory_cache, _redis_disabled_until
    _memory_cache.clear()
    _redis_disabled_until = 0.0


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
        await delete_cache_pattern("cache:collections:*")
    elif media_type in ("series", "season", "episode"):
        await delete_cache_pattern("cache:series:*")
        await delete_cache_pattern("cache:search:*")
        await delete_cache_pattern("cache:collections:*")
    else:
        await delete_cache_pattern("cache:movies:*")
        await delete_cache_pattern("cache:series:*")
        await delete_cache_pattern("cache:search:*")
        await delete_cache_pattern("cache:collections:*")
        await delete_cache_pattern("cache:*")
