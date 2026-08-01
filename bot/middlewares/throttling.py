import logging
import os
import time
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

logger = logging.getLogger(__name__)

# Try to import job_manager from backend to reuse the existing Redis pool
try:
    from app.core.job_manager import job_manager
    redis_client = job_manager._redis
except ImportError:
    logger.warning("Could not import job_manager from backend. Rate limiting might not share the same Redis pool.")
    import redis.asyncio as redis
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    redis_client = redis.from_url(redis_url, decode_responses=True)

class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self, limit_per_minute: int = None):
        super().__init__()
        # Use env var if provided, fallback to 20
        env_limit = os.environ.get("BOT_RATE_LIMIT_PER_MINUTE")
        if env_limit and env_limit.isdigit():
            self.limit = int(env_limit)
        else:
            self.limit = limit_per_minute or 20
        self.window = 60 # seconds

    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any]
    ) -> Any:
        
        user_id = None
        if isinstance(event, Message):
            user_id = event.from_user.id
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            
        if not user_id:
            return await handler(event, data)
            
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
                await redis_client.expire(key, self.window)
                
            if current_count > self.limit:
                # Limit exceeded
                warning_msg = "⏳ Iltimos, biroz kuting. Siz juda ko'p so'rov yubordingiz."
                if isinstance(event, Message):
                    await event.answer(warning_msg)
                elif isinstance(event, CallbackQuery):
                    await event.answer(warning_msg, show_alert=True)
                return # Stop processing
                
        except Exception as e:
            # If Redis fails, we should probably allow the request to pass rather than breaking the bot
            logger.error(f"Throttling Redis error: {e}")
            
        return await handler(event, data)
