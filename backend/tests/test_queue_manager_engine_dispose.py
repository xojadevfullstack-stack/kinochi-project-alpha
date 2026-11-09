import asyncio
from unittest.mock import patch, AsyncMock
import pytest
from sqlalchemy.ext.asyncio import AsyncEngine
from scraper.queue_manager import _run_coro_sync, QueueManager

@pytest.mark.asyncio
async def test_run_coro_sync_disposes_engine_before_closing_thread_loop():
    """
    BUG-008 Regression Test (Async caller context):
    When _run_coro_sync is executed while an event loop is running (delegating
    to ThreadPoolExecutor with an ephemeral event loop), any null_engine
    attached to loop._kinochi_loop_session_factory MUST be disposed before
    the loop is closed.
    """
    real_dispose = AsyncEngine.dispose
    dispose_calls = []

    async def spy_dispose(self, *args, **kwargs):
        dispose_calls.append(self)
        return await real_dispose(self, *args, **kwargs)

    async def sample_coro():
        factory = QueueManager._get_nullpool_session_factory()
        engine = factory.kw["bind"]
        return engine

    with patch.object(AsyncEngine, "dispose", side_effect=spy_dispose, autospec=True):
        engine = _run_coro_sync(sample_coro())
        assert engine is not None
        assert len(dispose_calls) == 1, (
            f"Engine was not disposed before thread loop shutdown! Disposed count: {len(dispose_calls)}"
        )


def test_run_coro_sync_disposes_engine_in_sync_context():
    """
    BUG-008 Regression Test (Sync caller context):
    When _run_coro_sync is executed with no running event loop, any null_engine
    attached to the ephemeral loop's session factory MUST be disposed.
    """
    real_dispose = AsyncEngine.dispose
    dispose_calls = []

    async def spy_dispose(self, *args, **kwargs):
        dispose_calls.append(self)
        return await real_dispose(self, *args, **kwargs)

    async def sample_coro():
        factory = QueueManager._get_nullpool_session_factory()
        engine = factory.kw["bind"]
        return engine

    with patch.object(AsyncEngine, "dispose", side_effect=spy_dispose, autospec=True):
        engine = _run_coro_sync(sample_coro())
        assert engine is not None
        assert len(dispose_calls) == 1, (
            f"Engine was not disposed before sync loop shutdown! Disposed count: {len(dispose_calls)}"
        )
