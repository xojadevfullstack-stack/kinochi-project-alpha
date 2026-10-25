import logging
import os
import time
from typing import Any, Awaitable, Callable, Dict, List

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, InlineQuery, InlineQueryResultsButton

logger = logging.getLogger(__name__)

# Try to import job_manager from backend to reuse the existing Redis pool
redis_client = None
try:
    from app.core.job_manager import job_manager
    redis_client = job_manager._redis
except ImportError:
    try:
        import redis.asyncio as redis
        redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url, decode_responses=True)
    except Exception as e:
        logger.warning(f"Could not initialize Redis client for throttling: {e}")
        redis_client = None

# Fallback in-memory rate limiter when Redis is down/misconfigured
_memory_rate_limits: Dict[int, List[float]] = {}
_redis_disabled_until: float = 0.0
_REDIS_COOLDOWN = 300.0  # If Redis fails, disable Redis attempts for 5 minutes

# If REDIS_URL has known dummy placeholders, disable immediately without waiting for timeout
_redis_url_str = os.environ.get("REDIS_URL", "")
if "SIZNING_UPSTASH_PAROLINGIZ" in _redis_url_str or "parol" in _redis_url_str.lower():
    _redis_disabled_until = float("inf")
    logger.info("ThrottlingMiddleware: Placeholder REDIS_URL detected, defaulting to fast in-memory rate limiter.")

def _check_memory_rate_limit(user_id: int, limit: int, window: float = 60.0) -> bool:
    """Returns True if user is allowed, False if rate limited."""
    now = time.monotonic()
    timestamps = _memory_rate_limits.setdefault(user_id, [])
    cutoff = now - window
    valid_timestamps = [t for t in timestamps if t > cutoff]
    _memory_rate_limits[user_id] = valid_timestamps
    if len(valid_timestamps) >= limit:
        return False
    valid_timestamps.append(now)
    # Cleanup memory periodically if dictionary gets large
    if len(_memory_rate_limits) > 5000:
        for uid in list(_memory_rate_limits.keys()):
            if not _memory_rate_limits[uid] or _memory_rate_limits[uid][-1] <= cutoff:
                _memory_rate_limits.pop(uid, None)
    return True


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit_per_minute: int = None):
        super().__init__()
        # Use env var if provided, fallback to 20
        env_limit = os.environ.get("BOT_RATE_LIMIT_PER_MINUTE")
        if env_limit and env_limit.isdigit():
            self.limit = int(env_limit)
        else:
            self.limit = limit_per_minute or 20
        self.window = 60.0  # seconds

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any]
    ) -> Any:
        global _redis_disabled_until
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id if event.from_user else None
        elif isinstance(event, InlineQuery):
            user_id = event.from_user.id if event.from_user else None

        if not user_id:
            return await handler(event, data)

        now = time.monotonic()
        use_redis = (redis_client is not None) and (now > _redis_disabled_until)

        if use_redis:
            key = f"ratelimit:{user_id}"
            try:
                # We use an atomic pipeline to increment and set expiration
                async with redis_client.pipeline(transaction=True) as pipe:
                    await pipe.incr(key)
                    await pipe.ttl(key)
                    results = await pipe.execute()

                current_count = results[0]
                ttl = results[1]

                # If the key was just created (ttl is -1 or -2), set expiration
                if ttl < 0:
                    await redis_client.expire(key, int(self.window))

                if current_count > self.limit:
                    warning_msg = "⏳ Iltimos, biroz kuting. Siz juda ko'p so'rov yubordingiz."
                    if isinstance(event, Message):
                        await event.answer(warning_msg)
                    elif isinstance(event, CallbackQuery):
                        await event.answer(warning_msg, show_alert=True)
                    elif isinstance(event, InlineQuery):
                        try:
                            await event.answer([], cache_time=5, is_personal=True, button=InlineQueryResultsButton(text="⏳ Iltimos, biroz kuting...", start_parameter="throttled"))
                        except Exception:
                            pass
                    return
                return await handler(event, data)

            except Exception as e:
                _redis_disabled_until = time.monotonic() + _REDIS_COOLDOWN
                logger.warning(f"Throttling Redis error: {e}. Switching to in-memory rate limiter for {_REDIS_COOLDOWN}s.")

        # In-memory fallback
        allowed = _check_memory_rate_limit(user_id, self.limit, self.window)
        if not allowed:
            warning_msg = "⏳ Iltimos, biroz kuting. Siz juda ko'p so'rov yubordingiz."
            if isinstance(event, Message):
                await event.answer(warning_msg)
            elif isinstance(event, CallbackQuery):
                await event.answer(warning_msg, show_alert=True)
            elif isinstance(event, InlineQuery):
                try:
                    await event.answer([], cache_time=5, is_personal=True, button=InlineQueryResultsButton(text="⏳ Iltimos, biroz kuting...", start_parameter="throttled"))
                except Exception:
                    pass
            return

        return await handler(event, data)
