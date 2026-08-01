import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../bot')))
from middlewares.throttling import ThrottlingMiddleware
from aiogram.types import Message, User, Chat

# Try to mock the Redis backend for throttling
class MockRedisPipeline:
    def __init__(self, state):
        self.state = state
        self.key = None

    async def incr(self, key):
        self.key = key
        if key not in self.state:
            self.state[key] = {'count': 0, 'ttl': -1}
        self.state[key]['count'] += 1

    async def ttl(self, key):
        pass

    async def execute(self):
        # returns [current_count, ttl]
        return [self.state[self.key]['count'], self.state[self.key]['ttl']]

    async def __aenter__(self):
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class MockRedisClient:
    def __init__(self):
        self.state = {}
        
    def pipeline(self, transaction=True):
        return MockRedisPipeline(self.state)
        
    async def expire(self, key, time):
        self.state[key]['ttl'] = time

@pytest.mark.asyncio
async def test_throttling_middleware():
    import middlewares.throttling
    # Patch the redis_client inside the throttling module
    original_redis = middlewares.throttling.redis_client
    middlewares.throttling.redis_client = MockRedisClient()

    try:
        middleware = ThrottlingMiddleware(limit_per_minute=2)
        
        # Mock message event
        mock_handler = AsyncMock(return_value="Passed")
        mock_message = MagicMock(spec=Message)
        mock_message.from_user = User(id=123, is_bot=False, first_name="Test")
        mock_message.answer = AsyncMock()
        
        # Request 1 (count 1 <= 2)
        res1 = await middleware(mock_handler, mock_message, {})
        assert res1 == "Passed"
        mock_handler.assert_awaited_once()
        mock_handler.reset_mock()
        
        # Request 2 (count 2 <= 2)
        res2 = await middleware(mock_handler, mock_message, {})
        assert res2 == "Passed"
        mock_handler.assert_awaited_once()
        mock_handler.reset_mock()
        
        # Request 3 (count 3 > 2) -> Throttled
        res3 = await middleware(mock_handler, mock_message, {})
        assert res3 is None
        mock_handler.assert_not_awaited()
        mock_message.answer.assert_awaited_once()
        assert "juda ko'p so'rov" in mock_message.answer.call_args[0][0]
        mock_message.answer.reset_mock()
        
        # Simulate expiry
        middlewares.throttling.redis_client.state.clear()
        
        # Request 4 (count 1 <= 2)
        res4 = await middleware(mock_handler, mock_message, {})
        assert res4 == "Passed"
        mock_handler.assert_awaited_once()

    finally:
        middlewares.throttling.redis_client = original_redis
