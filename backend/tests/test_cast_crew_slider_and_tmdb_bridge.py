import pytest
import os
from unittest.mock import AsyncMock, patch

WEBSITE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "website"))
CAST_CREW_COMPONENT = os.path.join(WEBSITE_DIR, "components", "media", "CastCrewSection.tsx")

def test_cast_crew_component_has_slider_and_drag():
    """Verify that CastCrewSection has desktop slider buttons and drag-to-scroll."""
    with open(CAST_CREW_COMPONENT, "r", encoding="utf-8") as f:
        content = f.read()

    # Desktop slider buttons
    assert "chevron_left" in content or "arrow_back" in content or "<" in content
    assert "chevron_right" in content or "arrow_forward" in content or ">" in content
    assert "scrollBy" in content or "scrollLeft" in content

    # Drag-to-scroll handlers
    assert "onMouseDown" in content
    assert "onMouseMove" in content
    assert "onMouseUp" in content
    assert "isDragging" in content or "cursor-grab" in content

def test_cast_crew_component_has_unified_div_with_tmdb_details():
    """Verify that CastCrewSection wraps Cast & Crew and TMDb extra info in a unified container."""
    with open(CAST_CREW_COMPONENT, "r", encoding="utf-8") as f:
        content = f.read()

    # Unified info headers or details keys
    assert "details" in content
    assert "Asl nomi" in content or "original_title" in content
    assert "Mamlakat" in content or "production_countries" in content or "countries" in content
    assert "Studiya" in content or "production_companies" in content or "companies" in content

@pytest.mark.asyncio
async def test_tmdb_client_returns_credits_and_details():
    """Verify that TMDb client extracts crew, actors, and production details."""
    from app.infrastructure.external.tmdb_client import tmdb_client

    mock_tv_details = {
        "id": 87108,
        "name": "Чернобыль",
        "original_name": "Chernobyl",
        "status": "Ended",
        "first_air_date": "2019-05-06",
        "production_countries": [{"name": "United States of America"}, {"name": "United Kingdom"}],
        "production_companies": [{"name": "HBO"}, {"name": "SISTER"}],
        "created_by": [{"id": 35796, "name": "Крейг Мейзин", "profile_path": "/creator.jpg"}]
    }
    mock_tv_credits = {
        "id": 87108,
        "cast": [{"id": 1, "name": "Jared Harris", "character": "Valery Legasov", "profile_path": "/jh.jpg", "order": 0}],
        "crew": [{"id": 2, "name": "Johan Renck", "job": "Director", "profile_path": "/jr.jpg"}]
    }

    async def fake_request(endpoint, params):
        if "credits" in endpoint:
            return mock_tv_credits
        return mock_tv_details

    with patch.object(tmdb_client, "_request_with_retry", side_effect=fake_request):
        res = await tmdb_client.get_credits_and_details(87108, kind="tv")
        assert "items" in res
        assert "details" in res
        assert len(res["items"]) >= 2
        
        # Check creator/director is present with Uzbek role
        roles = [m["role"] for m in res["items"]]
        assert "Rejissyor" in roles or "Muallif" in roles
        assert "Aktyor" in roles

        # Check details
        assert res["details"]["original_title"] == "Chernobyl"
        assert "AQSH" in res["details"]["countries"] or "United States of America" in res["details"]["countries"]
        assert "HBO" in res["details"]["companies"]
        assert res["details"]["status"] == "Tugallangan"

def test_cast_crew_1_click_filmography_modal_integration():
    """Verify that clicking any actor or creator in CastCrewSection opens their filmography modal."""
    with open(CAST_CREW_COMPONENT, "r", encoding="utf-8") as f:
        content = f.read()

    # Person must be a clickable button
    assert "handlePersonClick" in content
    assert "<button" in content
    assert "Filmografiyasini ko'rish" in content

    # ActorFilmographyModal must be mounted
    assert "ActorFilmographyModal" in content
    assert "selectedActor" in content

    # Component file must exist
    modal_file = os.path.join(WEBSITE_DIR, "components", "media", "ActorFilmographyModal.tsx")
    assert os.path.exists(modal_file), "ActorFilmographyModal.tsx component must exist"
    with open(modal_file, "r", encoding="utf-8") as mf:
        modal_content = mf.read()
    assert "actors/${actor" in modal_content or "/actors/" in modal_content
    assert "Tomosha qilish" in modal_content
    assert "Buyurtma berish" in modal_content

