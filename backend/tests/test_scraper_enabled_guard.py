import sys
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.api.deps import get_current_admin
import scraper.config as scraper_cfg
import scraper.run_scraper as run_scraper_mod
from scraper.process_manager import ProcessManager


@pytest.fixture
def admin_client():
    app.dependency_overrides[get_current_admin] = lambda: {"username": "admin", "role": "admin"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_current_admin, None)


def test_scraper_enabled_defaults_false(monkeypatch):
    monkeypatch.delenv("SCRAPER_ENABLED", raising=False)
    assert settings.SCRAPER_ENABLED is False
    assert scraper_cfg.is_scraper_enabled() is False


@pytest.mark.parametrize(
    "cli_args",
    [
        ["run_scraper.py", "--parse", "--source", "asilmedia", "--pages", "1"],
        ["run_scraper.py", "--download", "--target", "asilmedia", "--limit", "1"],
        ["run_scraper.py", "--autopilot", "--source", "asilmedia"],
        ["run_scraper.py", "--tmdb-autopilot"],
    ],
)
def test_run_scraper_cli_blocked_when_disabled(monkeypatch, capsys, cli_args):
    monkeypatch.setenv("SCRAPER_ENABLED", "false")
    monkeypatch.setattr(sys, "argv", cli_args)

    with pytest.raises(SystemExit) as exc_info:
        run_scraper_mod.main()

    assert exc_info.value.code != 0
    captured = capsys.readouterr()
    assert "SCRAPER_ENABLED=False" in captured.out


def test_run_scraper_cli_stats_and_help_allowed_when_disabled(monkeypatch, capsys):
    monkeypatch.setenv("SCRAPER_ENABLED", "false")

    with patch.object(run_scraper_mod, "cmd_stats") as mock_stats:
        monkeypatch.setattr(sys, "argv", ["run_scraper.py", "--stats"])
        run_scraper_mod.main()
        mock_stats.assert_called_once()

    monkeypatch.setattr(sys, "argv", ["run_scraper.py", "--help"])
    with pytest.raises(SystemExit) as exc_info:
        run_scraper_mod.main()
    assert exc_info.value.code == 0


def test_process_manager_blocked_when_disabled(monkeypatch):
    monkeypatch.setenv("SCRAPER_ENABLED", "false")
    pm = ProcessManager()
    pm.is_running = False

    with patch("subprocess.Popen") as mock_popen:
        r1 = pm.start_parse(source="asilmedia", pages=1)
        assert r1["success"] is False
        assert "SCRAPER_ENABLED" in r1["message"]

        r2 = pm.start_download(target="asilmedia", limit=1)
        assert r2["success"] is False
        assert "SCRAPER_ENABLED" in r2["message"]

        r3 = pm.start_autopilot(source="asilmedia")
        assert r3["success"] is False
        assert "SCRAPER_ENABLED" in r3["message"]

        mock_popen.assert_not_called()


def test_admin_api_scraper_start_endpoints_blocked_when_disabled(admin_client):
    with patch.object(settings, "AUTO_CONTENT_ENABLED", True), \
         patch.object(settings, "SCRAPER_ENABLED", False):
        resp1 = admin_client.post("/api/v1/scraper/start-parse", json={"source": "asilmedia", "pages": 1})
        assert resp1.status_code == 403
        assert "SCRAPER_ENABLED" in resp1.json()["detail"]

        resp2 = admin_client.post("/api/v1/scraper/start-download", json={"target": "asilmedia", "limit": 1})
        assert resp2.status_code == 403
        assert "SCRAPER_ENABLED" in resp2.json()["detail"]

        resp3 = admin_client.post("/api/v1/scraper/autopilot", json={"source": "asilmedia"})
        assert resp3.status_code == 403
        assert "SCRAPER_ENABLED" in resp3.json()["detail"]

        resp4 = admin_client.post("/api/v1/scraper/quick-grab", json={"id": "asilmedia_1", "source": "asilmedia", "title": "Test"})
        assert resp4.status_code == 403
        assert "SCRAPER_ENABLED" in resp4.json()["detail"]

        # Read-only status endpoint still works
        resp_status = admin_client.get("/api/v1/scraper/status")
        assert resp_status.status_code == 200
