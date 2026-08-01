import asyncio
import time
from httpx import AsyncClient, ASGITransport
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))
from app.main import app
from app.core.job_manager import job_manager
import fakeredis

async def test_cache():
    print("=== REDIS CACHE VERIFICATION ===")
    
    # Mock redis connection
    fake_redis = fakeredis.FakeAsyncRedis()
    job_manager._redis = fake_redis
    
    # Using AsyncClient to test the FastAPI app directly
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # First request - Cache MISS
        start_time = time.time()
        response1 = await client.get("/api/v1/movies")
        time1 = time.time() - start_time
        print(f"[MISS] First request time: {time1:.4f} soniya (Status: {response1.status_code})")
        
        # Second request - Cache HIT
        start_time = time.time()
        response2 = await client.get("/api/v1/movies")
        time2 = time.time() - start_time
        print(f"[HIT]  Second request time: {time2:.4f} soniya (Status: {response2.status_code})")
        
        speedup = time1 / time2 if time2 > 0 else float('inf')
        print(f"       Natija: Kesh bilan {speedup:.1f} marta tezroq ishladi!")

    # Verify keys exist in Redis
    try:
        keys = await job_manager._redis.keys("cache:movies:*")
        print("\n=== REDIS KEYS ===")
        print(f"Topilgan kalitlar soni: {len(keys)}")
        for k in keys:
            print(f"- {k.decode('utf-8')}")
    except Exception as e:
        print(f"Redis keys tekshirishda xatolik: {e}")

if __name__ == "__main__":
    asyncio.run(test_cache())
