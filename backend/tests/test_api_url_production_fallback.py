from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_api_ts_normalizes_dead_render_and_production_fallback():
    api_ts = (ROOT / "website" / "lib" / "api.ts").read_text(encoding="utf-8")
    assert "export const API_URL" in api_ts
    assert "https://kinochi-project-alpha-9g6j.onrender.com/api/v1" in api_ts
    assert "kinochi-project-alpha.onrender.com" in api_ts


def test_client_components_use_shared_api_url():
    for rel in [
        "website/components/LiveSearch.tsx",
        "website/components/ReportIssueModal.tsx",
        "website/components/RequestMovieModal.tsx",
        "website/app/requests/page.tsx",
    ]:
        content = (ROOT / rel).read_text(encoding="utf-8")
        assert "API_URL" in content
        assert 'from "@/lib/api"' in content or "from '../lib/api'" in content
