"""
Redis-backed Job Manager for background video upload tasks.
"""
import json
import uuid
import logging
from enum import Enum
from typing import Any, Dict, Optional
import redis.asyncio as redis
from redis.exceptions import RedisError
from fastapi import HTTPException
from app.core.config import settings

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class JobManager:
    def __init__(self):
        # We don't connect immediately. We pass timeout settings.
        self._redis = redis.from_url(
            settings.REDIS_URL, 
            decode_responses=True,
            socket_connect_timeout=3,
            socket_timeout=3
        )
        self._prefix = "job:"

    async def create_job(self, meta: Optional[Dict] = None) -> str:
        """Yangi job yaratib, uning ID sini qaytaradi."""
        job_id = str(uuid.uuid4())
        job_data = {
            "status": JobStatus.PENDING.value,
            "progress": 0,         # 0-100
            "result": None,        # muvaffaqiyatli bo'lganda natija
            "error": None,         # xato xabari
            "meta": meta or {},
        }
        try:
            await self._redis.setex(f"{self._prefix}{job_id}", 86400 * 3, json.dumps(job_data)) # 3 days TTL
            logger.info(f"Job created: {job_id}")
            return job_id
        except RedisError as e:
            logger.error(f"Redis ulanish xatosi (create_job): {e}")
            raise HTTPException(status_code=503, detail="Xizmat vaqtincha yopiq (Kesh xotira xatosi).")

    async def get_job(self, job_id: str) -> Optional[Dict]:
        try:
            data = await self._redis.get(f"{self._prefix}{job_id}")
            if data:
                return json.loads(data)
            return None
        except RedisError as e:
            logger.error(f"Redis ulanish xatosi (get_job): {e}")
            raise HTTPException(status_code=503, detail="Xizmat vaqtincha yopiq (Kesh xotira xatosi).")

    async def _update_job(self, job_id: str, updates: Dict):
        try:
            job = await self.get_job(job_id)
            if job:
                job.update(updates)
                await self._redis.setex(f"{self._prefix}{job_id}", 86400 * 3, json.dumps(job))
        except HTTPException:
            pass # Already logged in get_job
        except RedisError as e:
            logger.error(f"Redis ulanish xatosi (_update_job): {e}")

    async def set_processing(self, job_id: str, progress: int = 0):
        await self._update_job(job_id, {"status": JobStatus.PROCESSING.value, "progress": progress})

    async def set_progress(self, job_id: str, progress: int):
        await self._update_job(job_id, {"progress": min(progress, 99)})

    async def set_done(self, job_id: str, result: Any = None):
        await self._update_job(job_id, {"status": JobStatus.DONE.value, "progress": 100, "result": result})
        logger.info(f"Job done: {job_id}")

    async def set_failed(self, job_id: str, error: str):
        await self._update_job(job_id, {"status": JobStatus.FAILED.value, "error": error})
        logger.error(f"Job failed: {job_id} — {error}")

    async def cleanup_old_jobs(self, max_jobs: int = 200):
        """Eski joblarni tozalash. Redis TTL o'zi tozalaydi, shuning uchun bu pass qilinishi mumkin."""
        pass


# Global singleton
job_manager = JobManager()
