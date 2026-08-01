import json
import logging
from typing import Any, Optional
from redis.exceptions import RedisError
from app.core.job_manager import job_manager

logger = logging.getLogger(__name__)

async def get_cache(key: str) -> Optional[Any]:
    """Retrieve data from Redis cache."""
    try:
        data = await job_manager._redis.get(key)
        if data:
            return json.loads(data)
    except RedisError as e:
        logger.error(f"Redis get_cache error: {e}")
    except Exception as e:
        logger.error(f"Cache decode error for key {key}: {e}")
    return None

async def set_cache(key: str, data: Any, ttl_seconds: int = 300) -> bool:
    """Store data in Redis cache with TTL."""
    try:
        await job_manager._redis.setex(key, ttl_seconds, json.dumps(data))
        return True
    except RedisError as e:
        logger.error(f"Redis set_cache error: {e}")
    except Exception as e:
        logger.error(f"Cache encode error for key {key}: {e}")
    return False

async def delete_cache_pattern(pattern: str) -> None:
    """Delete keys matching a specific pattern (e.g., 'cache:movies:*')."""
    try:
        # For simplicity in async context, using keys + delete
        # For a massive database, HSCAN/SCAN would be better, but this is a lightweight cache
        keys = await job_manager._redis.keys(pattern)
        if keys:
            await job_manager._redis.delete(*keys)
    except RedisError as e:
        logger.error(f"Redis delete_cache_pattern error: {e}")
