import pytest
import time
import asyncio
from httpx import AsyncClient, ASGITransport

from app.main import app

@pytest.mark.asyncio
async def test_auth_rate_limiting():
    # Send 10 concurrent requests to /api/v1/auth/telegram-login
    # The limiter in Kinochi might be 5 per minute.
    
    payload = {
        "id": 1,
        "auth_date": int(time.time()),
        "hash": "invalid"
    }
    
    async def fetch(client):
        return await client.post("/api/v1/auth/telegram-login", json=payload)
        
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        tasks = [fetch(ac) for _ in range(35)]
        responses = await asyncio.gather(*tasks)
        
        status_codes = [resp.status_code for resp in responses]
        
        # We expect some 429s if rate limiting is working properly
        num_429s = status_codes.count(429)
        num_401s = status_codes.count(401)  # Invalid hash returns 401
        
        print(f"Total requests: 35")
        print(f"401 Unauthorized (processed): {num_401s}")
        print(f"429 Too Many Requests (blocked): {num_429s}")
        
        # Assert rate limiting worked
        assert num_429s > 0, "Rate limit was not applied! No 429s received."
