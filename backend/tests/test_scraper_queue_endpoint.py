import inspect
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_admin
from app.api.v1.scraper import get_queue, get_status, clear_all_queue
from scraper.queue_manager import QueueItem


@pytest.fixture
def admin_client():
    app.dependency_overrides[get_current_admin] = lambda: {"username": "admin", "role": "admin"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_current_admin, None)


def test_scraper_queue_and_status_handlers_are_async():
    """get_queue, get_status and clear_all_queue must be async def handlers to avoid threadpool loop detachment."""
    assert inspect.iscoroutinefunction(get_queue), "get_queue must be an async def handler"
    assert inspect.iscoroutinefunction(get_status), "get_status must be an async def handler"
    assert inspect.iscoroutinefunction(clear_all_queue), "clear_all_queue must be an async def handler"


def test_scraper_queue_endpoint_returns_items(admin_client):
    """GET /api/v1/scraper/queue must return items without event loop collision."""
    mock_items = [
        QueueItem(
            id="asilmedia_123",
            source="asilmedia",
            title="Naruto",
            media_type="anime",
            year=2002,
            status="pending",
        )
    ]
    with patch("scraper.queue_manager.QueueManager.get_filtered_async", new_callable=AsyncMock) as mock_filt, \
         patch("scraper.queue_manager.QueueManager.stats_async", new_callable=AsyncMock) as mock_stats:
        mock_filt.return_value = (mock_items, 1)
        mock_stats.return_value = {"total": 1, "pending": 1, "completed": 0, "failed": 0}

        resp = admin_client.get("/api/v1/scraper/queue?status=all&source=all&media_type=all")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["title"] == "Naruto"
        mock_filt.assert_awaited_once()
        mock_stats.assert_awaited_once()


def test_scraper_queue_clear_all_not_blocked(admin_client):
    """POST /api/v1/scraper/queue/clear-all must check is_running attribute and succeed when idle."""
    mock_pm = MagicMock()
    mock_pm.is_running = False
    with patch("scraper.queue_manager.QueueManager.clear_all_async", new_callable=AsyncMock) as mock_clear, \
         patch("app.api.v1.scraper.ProcessManager", return_value=mock_pm):
        mock_clear.return_value = 42

        resp = admin_client.post("/api/v1/scraper/queue/clear-all")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["count"] == 42
        mock_clear.assert_awaited_once()


def test_scraper_queue_clear_all_forbids_while_running(admin_client):
    """POST /api/v1/scraper/queue/clear-all must raise 409 if process is running."""
    mock_pm = MagicMock()
    mock_pm.is_running = True
    with patch("app.api.v1.scraper.ProcessManager", return_value=mock_pm):
        resp = admin_client.post("/api/v1/scraper/queue/clear-all")
        assert resp.status_code == 409
        assert "ishlayotgan paytda" in resp.json()["detail"]
