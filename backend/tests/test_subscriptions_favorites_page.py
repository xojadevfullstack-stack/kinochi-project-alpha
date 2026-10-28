import pytest
import os

WEBSITE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "website"))
SUBSCRIPTIONS_PAGE = os.path.join(WEBSITE_DIR, "app", "subscriptions", "page.tsx")

def test_subscriptions_page_removes_mock_vip_tariffs():
    """Verify that subscriptions/page.tsx does not contain paid VIP money mock tariffs."""
    with open(SUBSCRIPTIONS_PAGE, "r", encoding="utf-8") as f:
        content = f.read()

    # Must remove mock money prices
    assert "25,000 so'm" not in content
    assert "65,000 so'm" not in content
    assert "220,000 so'm" not in content
    assert "TARIFFS" not in content
    assert "1 Oylik VIP" not in content

def test_subscriptions_page_supports_real_user_subscriptions():
    """Verify that subscriptions page fetches and displays user's subscribed series and collections."""
    with open(SUBSCRIPTIONS_PAGE, "r", encoding="utf-8") as f:
        content = f.read()

    # Must be interactive client component
    assert '"use client"' in content or "'use client'" in content

    # Must query subscriptions API or state
    assert "/users/me/subscriptions" in content or "subscriptions" in content
    assert "series" in content
    assert "collections" in content

    # Must have clean empty state
    assert "Hozircha obunalar yo'q" in content or "obuna" in content.lower()
