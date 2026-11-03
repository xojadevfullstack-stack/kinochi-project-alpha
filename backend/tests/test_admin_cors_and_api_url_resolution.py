import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_cors_origin_regex_allows_vercel_deployments():
    """Vercel preview va production domenlari uchun CORS ruxsati bo'lishi kerak."""
    from app.core.config import Settings

    s = Settings()
    assert s.CORS_ORIGIN_REGEX is not None, "CORS_ORIGIN_REGEX None bo'lmasligi kerak"
    pattern = re.compile(s.CORS_ORIGIN_REGEX)
    assert pattern.match("https://kinochi-project-alpha.vercel.app")
    assert pattern.match("https://kinochi-project-alpha-iia3u82l1.vercel.app")
    assert pattern.match("https://kinochi-admin.vercel.app")
    assert not pattern.match("https://malicious-site.com")


def test_admin_panel_api_url_resolution_and_dead_render_replacement():
    """admin-panel/lib/api.ts va app/login/page.tsx to'g'ri API_URL ga murojaat qilishi kerak."""
    api_ts = (ROOT / "admin-panel" / "lib" / "api.ts").read_text(encoding="utf-8")
    assert "https://kinochi-project-alpha-9g6j.onrender.com" in api_ts
    assert "kinochi-project-alpha.onrender.com" in api_ts

    login_page = (ROOT / "admin-panel" / "app" / "login" / "page.tsx").read_text(encoding="utf-8")
    assert "API_URL" in login_page
    assert 'from "@/lib/api"' in login_page or "from '../../lib/api'" in login_page
