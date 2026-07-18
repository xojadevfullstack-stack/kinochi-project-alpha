import asyncio
import os
import sys

# Setup mock env to point to a dead redis
os.environ["REDIS_URL"] = "redis://localhost:9999/0" # wrong port

# Append backend path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.core.job_manager import job_manager
from fastapi import HTTPException

async def test_redis_down():
    try:
        print("Testing create_job with down Redis...")
        await job_manager.create_job({"test": "data"})
        print("FAIL: create_job did not raise HTTPException")
    except HTTPException as e:
        print(f"SUCCESS: create_job raised HTTPException gracefully. Status: {e.status_code}, Detail: {e.detail}")
    except Exception as e:
        print(f"FAIL: create_job raised unexpected exception: {type(e)} - {e}")

if __name__ == "__main__":
    asyncio.run(test_redis_down())
