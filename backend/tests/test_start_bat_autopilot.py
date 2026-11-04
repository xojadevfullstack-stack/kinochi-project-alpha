from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]


def test_start_bat_supports_admin_panel_default_and_autopilot():
    bat_path = ROOT_DIR / "start.bat"
    assert bat_path.exists(), "start.bat topilmadi"
    content = bat_path.read_text(encoding="utf-8")

    # 1. Default tanlov 1 (Admin Panel + Backend -> /scraper) bo'lishi kerak
    assert "set choice=1" in content
    assert "http://localhost:3001/scraper" in content

    # 2. Avtopilot va TMDb Avtopilot opsiyalari mavjud bo'lishi kerak
    assert "--autopilot" in content
    assert "--tmdb-autopilot" in content
    assert ":opt_autopilot" in content
    assert ":opt_tmdb_autopilot" in content
