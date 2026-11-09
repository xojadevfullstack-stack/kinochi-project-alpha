import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient

from app.main import app
from app.api.deps import get_current_admin


@pytest.fixture
def admin_client():
    app.dependency_overrides[get_current_admin] = lambda: {"username": "admin", "role": "admin"}
    client = TestClient(app)
    yield client
    app.dependency_overrides.pop(get_current_admin, None)


def test_content_lookup_translate_endpoint(admin_client):
    """POST /api/v1/content-lookup/translate translates title and description to Uzbek."""
    with patch("app.infrastructure.external.translator.translator_service.translate_title_to_uzbek", new_callable=AsyncMock) as mock_t, \
         patch("app.infrastructure.external.translator.translator_service.translate_to_uzbek", new_callable=AsyncMock) as mock_d:
        mock_t.return_value = ("Minora 2", True)
        mock_d.return_value = ("Tog'da halokatli sinov...", True)

        resp = admin_client.post(
            "/api/v1/content-lookup/translate",
            json={
                "title": "Вышка 2",
                "original_title": "Fall 2: Deadpoint",
                "description": "Опасное испытание на горе...",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Minora 2"
        assert data["description"] == "Tog'da halokatli sinov..."
        assert data["original_title"] == "Fall 2: Deadpoint"
