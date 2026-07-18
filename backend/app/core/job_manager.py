"""
In-memory Job Manager for background video upload tasks.

Job holatlari:
  pending    -> task navbatda
  processing -> Telegram'ga yuklanmoqda
  done       -> muvaffaqiyatli tugadi
  failed     -> xato yuz berdi
"""
import asyncio
import uuid
import logging
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"


class JobManager:
    def __init__(self):
        self._jobs: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def create_job(self, meta: Optional[Dict] = None) -> str:
        """Yangi job yaratib, uning ID sini qaytaradi."""
        job_id = str(uuid.uuid4())
        async with self._lock:
            self._jobs[job_id] = {
                "status": JobStatus.PENDING,
                "progress": 0,         # 0-100
                "result": None,        # muvaffaqiyatli bo'lganda natija
                "error": None,         # xato xabari
                "meta": meta or {},
            }
        logger.info(f"Job created: {job_id}")
        return job_id

    async def get_job(self, job_id: str) -> Optional[Dict]:
        async with self._lock:
            return dict(self._jobs.get(job_id, {}))

    async def set_processing(self, job_id: str, progress: int = 0):
        async with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = JobStatus.PROCESSING
                self._jobs[job_id]["progress"] = progress

    async def set_progress(self, job_id: str, progress: int):
        async with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["progress"] = min(progress, 99)

    async def set_done(self, job_id: str, result: Any = None):
        async with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = JobStatus.DONE
                self._jobs[job_id]["progress"] = 100
                self._jobs[job_id]["result"] = result
        logger.info(f"Job done: {job_id}")

    async def set_failed(self, job_id: str, error: str):
        async with self._lock:
            if job_id in self._jobs:
                self._jobs[job_id]["status"] = JobStatus.FAILED
                self._jobs[job_id]["error"] = error
        logger.error(f"Job failed: {job_id} — {error}")

    async def cleanup_old_jobs(self, max_jobs: int = 200):
        """Eski joblarni tozalash (xotira tejash uchun)."""
        async with self._lock:
            if len(self._jobs) > max_jobs:
                # Done/failed joblarni o'chir
                to_delete = [
                    jid for jid, j in self._jobs.items()
                    if j["status"] in (JobStatus.DONE, JobStatus.FAILED)
                ]
                for jid in to_delete[:len(self._jobs) - max_jobs]:
                    del self._jobs[jid]


# Global singleton
job_manager = JobManager()
