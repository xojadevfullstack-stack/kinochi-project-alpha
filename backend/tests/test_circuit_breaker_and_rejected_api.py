"""
Unit tests for Circuit Breaker and Rejected Items API (B4).
Verifies:
1. CircuitBreaker trips ONLY on infrastructure errors (FloodWait, bot no-reply, DB error)
2. Content defects are non-blocking and do not trip CircuitBreaker
3. Rejected items API endpoints (list, retry, blacklist)
"""
import os
import sys
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient
from scraper.autopilot_v2.health_evaluator import HealthEvaluator
from scraper.autopilot_v2.engine import AutopilotEngine
from app.main import app
from app.api.deps import get_current_admin, get_db_session
from app.infrastructure.db.models.rejected_item import RejectedItemModel


def test_circuit_breaker_ignores_content_defects():
    """Kontent kamchiliklari CircuitBreaker'ni to'xtatmasligini tekshirish."""
    evaluator = HealthEvaluator(min_sample_size=5, pause_threshold_percent=90.0)

    # 10 ta nuqsonli kontentni baholash
    defective_item = {
        "title": "A",
        "genres": [],
        "description": "Short",
        "source": "invalid",
    }
    for _ in range(10):
        res = evaluator.evaluate_item(defective_item)
        assert res.is_healthy is False

    # CircuitBreaker hali ham to'xtamagan bo'lishi kerak, chunki infratuzilma xatosi emas
    status = evaluator.check_circuit_breaker()
    assert status.is_paused is False
    assert len(evaluator.history) == 0


def test_circuit_breaker_trips_on_infrastructure_failures():
    """Infratuzilma xatolari (FloodWait, bot javobsiz, DB xato) CircuitBreaker'ni to'xtatishini tekshirish."""
    evaluator = HealthEvaluator(min_sample_size=5, pause_threshold_percent=90.0)

    # 5 ta ketma-ket infratuzilma xatosi qayd etish
    for _ in range(5):
        evaluator.record_infrastructure_failure("FloodWaitError", "Telegram 429")

    status = evaluator.check_circuit_breaker()
    assert status.is_paused is True
    assert "Infratuzilma salomatligi" in (status.pause_reason or "")

    # Muvaffaqiyatli tiklanish
    evaluator.manual_resume()
    status_resumed = evaluator.check_circuit_breaker()
    assert status_resumed.is_paused is False


def test_autopilot_engine_non_blocking_on_content_defects():
    """AutopilotEngine nuqsonli kontentda to'xtab qolmasdan keyingisiga o'tishini tekshirish."""
    engine = AutopilotEngine()
    engine.health_evaluator.history = []
    engine.health_evaluator.is_paused = False

    raw_defective = {
        "title": "A",
        "source": "invalid",
        "description": "Short",
    }

    # Bitta nuqsonli elementni kiritish
    ok, msg, item = engine.process_incoming_media(raw_defective)
    assert ok is False
    assert "karantinga olindi" in msg.lower()

    # Engine hali ham ishchi holatda ekanligini assert qilish
    cb = engine.health_evaluator.check_circuit_breaker()
    assert cb.is_paused is False


def test_rejected_items_api_endpoints():
    """Rejected items API (GET /rejected, POST /{id}/retry, POST /{id}/blacklist) tekshirish."""
    client = TestClient(app)

    async def mock_admin():
        return {"id": 1, "username": "superadmin", "role": "admin"}

    mock_db = AsyncMock()
    mock_item = RejectedItemModel(
        id=42,
        media_type="movie",
        source="uzmovi",
        source_key="uz_42",
        title="Test Movie",
        payload={"url": "http://test.com"},
        defects=[{"field": "poster_url", "code": "unreachable", "message": "Failed"}],
        attempts=1,
        status="rejected"
    )
    mock_db.get.return_value = mock_item

    mock_exec_res = MagicMock()
    mock_exec_res.scalars.return_value.all.return_value = [mock_item]
    mock_db.execute.return_value = mock_exec_res
    mock_db.scalar.return_value = 1

    app.dependency_overrides[get_current_admin] = mock_admin
    app.dependency_overrides[get_db_session] = lambda: mock_db

    try:
        # 1. GET /api/v1/rejected
        res_list = client.get("/api/v1/rejected")
        assert res_list.status_code == 200
        data = res_list.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["id"] == 42

        # 2. POST /api/v1/rejected/42/retry
        res_retry = client.post("/api/v1/rejected/42/retry")
        assert res_retry.status_code == 200
        assert mock_item.status == "resolved"

        # 3. POST /api/v1/rejected/42/blacklist
        res_bl = client.post("/api/v1/rejected/42/blacklist")
        assert res_bl.status_code == 200
        assert mock_item.status == "blacklisted"
    finally:
        app.dependency_overrides.clear()
