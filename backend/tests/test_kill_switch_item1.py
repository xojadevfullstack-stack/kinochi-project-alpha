import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.api.deps import get_current_admin


@pytest.fixture
def admin_client():
    app.dependency_overrides[get_current_admin] = lambda: {"username": "admin", "role": "admin"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_current_admin, None)


def test_scraper_and_bulk_endpoints_blocked_when_auto_content_disabled(admin_client):
    """AUTO_CONTENT_ENABLED=False bo'lganda scraper va ommaviy import endpointlari 403 qaytarishi shart."""
    with patch.object(settings, "AUTO_CONTENT_ENABLED", False):
        # 1. Scraper start-download
        resp = admin_client.post("/api/v1/scraper/start-download", json={"target": "uzmovi", "limit": 5})
        assert resp.status_code == 403
        assert "AUTO_CONTENT_ENABLED o'chirilgan" in resp.json()["detail"]

        # 2. Scraper autopilot
        resp = admin_client.post("/api/v1/scraper/autopilot", json={"source": "all"})
        assert resp.status_code == 403
        assert "AUTO_CONTENT_ENABLED o'chirilgan" in resp.json()["detail"]

        # 3. Scraper quick-grab
        resp = admin_client.post("/api/v1/scraper/quick-grab", json={"id": "uz_1", "source": "uzmovi", "title": "Test"})
        assert resp.status_code == 403

        # 4. Scraper upload-batch
        resp = admin_client.post("/api/v1/scraper/upload-batch", json={"items": []})
        assert resp.status_code == 403

        # 5. Movies bulk-import
        resp = admin_client.post("/api/v1/movies/bulk-import", json={"items": [{"title": "Film 1"}]})
        assert resp.status_code == 403
        assert "AUTO_CONTENT_ENABLED o'chirilgan" in resp.json()["detail"]

        # 6. Series bulk-import
        resp = admin_client.post("/api/v1/series/bulk-import", json={"items": [{"title": "Serial 1"}]})
        assert resp.status_code == 403
        assert "AUTO_CONTENT_ENABLED o'chirilgan" in resp.json()["detail"]


def test_bulk_endpoints_allowed_when_auto_content_enabled(admin_client):
    """AUTO_CONTENT_ENABLED=True bo'lganda ommaviy import va scraper upload ruxsat berilishi kerak."""
    with patch.object(settings, "AUTO_CONTENT_ENABLED", True):
        resp = admin_client.post("/api/v1/movies/bulk-import", json={"items": [{"title": "Film 1"}]})
        assert resp.status_code == 201
        assert resp.json()["count"] == 1

        resp = admin_client.post("/api/v1/series/bulk-import", json={"items": [{"title": "Serial 1"}]})
        assert resp.status_code == 201
        assert resp.json()["count"] == 1

        resp = admin_client.post("/api/v1/scraper/upload-batch", json={"items": [{"title": "Item 1"}]})
        assert resp.status_code == 200
        assert resp.json()["count"] == 1


@pytest.mark.asyncio
async def test_seed_ingestor_enqueue_blocked_when_auto_content_disabled():
    """TMDb Top Seed Ingestor AUTO_CONTENT_ENABLED=False bo'lganda nomzodlarni navbatga qo'ymasligi shart."""
    from scraper.tmdb_top_ingestor import TmdbTopIngestor
    ingestor = TmdbTopIngestor(queue_manager=MagicMock())
    with patch("scraper.tmdb_top_ingestor.settings.AUTO_CONTENT_ENABLED", False):
        stats = await ingestor.enqueue_candidates(limit=5, execute=True)
        assert stats["enqueued"] == 0
        assert stats["found_ready"] == 0
