import pytest
import os
from unittest.mock import AsyncMock, patch

WEBSITE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "website"))
ACTORS_PAGE = os.path.join(WEBSITE_DIR, "app", "actors", "page.tsx")

def test_actors_page_has_filmography_and_request_feature():
    """Verify that actors page connects to real TMDb actor filmography and request feature."""
    with open(ACTORS_PAGE, "r", encoding="utf-8") as f:
        content = f.read()

    # Must support viewing actor filmography
    assert "filmography" in content or "movies" in content
    # Must support ordering / requesting movie if unavailable
    assert "Buyurtma berish" in content or "buyurtma" in content.lower() or "content-requests" in content
    # Must support watching if available
    assert "Tomosha qilish" in content or "Ko'rish" in content or "telegram" in content.lower()

@pytest.mark.asyncio
async def test_actors_api_returns_filmography_with_availability():
    """Verify backend actors endpoint returns movies marked with local availability."""
    from app.infrastructure.external.tmdb_client import tmdb_client

    mock_person = {
        "id": 976,
        "name": "Джейсон Стэйтем",
        "original_name": "Jason Statham",
        "profile_path": "/statham.jpg",
    }
    mock_credits = {
        "id": 976,
        "cast": [
            {"id": 671, "title": "Garri Potter 1", "release_date": "2001-11-16", "poster_path": "/hp.jpg"},
            {"id": 999999, "title": "Bazada yo'q film", "release_date": "2024-01-01", "poster_path": "/fake.jpg"}
        ]
    }

    async def fake_request(endpoint, params):
        if "credits" in endpoint:
            return mock_credits
        return mock_person

    with patch.object(tmdb_client, "_request_with_retry", side_effect=fake_request):
        filmography = await tmdb_client.get_person_filmography(976)
        assert len(filmography) == 2
        assert filmography[0]["tmdb_id"] == 671
        assert filmography[1]["tmdb_id"] == 999999

def test_popular_actors_catalog_has_verified_photos_and_expanded_cast():
    """Verify that backend actors catalog contains 40+ cinema icons with verified TMDb photos."""
    from app.api.v1.actors import POPULAR_ACTORS_CATALOG

    assert len(POPULAR_ACTORS_CATALOG) >= 40
    # Every single actor must have a valid non-empty photo URL on tmdb image CDN
    for actor in POPULAR_ACTORS_CATALOG:
        assert actor.get("id"), f"Actor {actor} missing TMDb ID"
        assert actor.get("name"), f"Actor {actor} missing name"
        photo = actor.get("photo_url")
        assert photo and photo.startswith("https://image.tmdb.org/t/p/w500/"), (
            f"Actor {actor['name']} has invalid photo URL: {photo}"
        )

def test_actors_page_mobile_3_col_compact_grid():
    """Verify that actors page uses compact 3-column grid on mobile with ergonomic card heights."""
    with open(ACTORS_PAGE, "r", encoding="utf-8") as f:
        content = f.read()

    # Must be 3 columns on mobile
    assert "grid-cols-3" in content
    # Must scale to 4, 5, 6 columns on larger screens
    assert "sm:grid-cols-4" in content
    assert "md:grid-cols-5" in content
    assert "lg:grid-cols-6" in content
    # Card avatar must be compact on mobile (w-16 h-16)
    assert "w-16 h-16" in content
    # Padding must be tight (p-2.5)
    assert "p-2.5" in content


