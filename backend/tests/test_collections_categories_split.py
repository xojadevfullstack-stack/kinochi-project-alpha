import pytest
import os

WEBSITE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "website"))
CLIENT_VIEW = os.path.join(WEBSITE_DIR, "components", "CollectionsClientView.tsx")
CATALOG_THEMES = os.path.join(WEBSITE_DIR, "lib", "catalogThemes.ts")

def test_collections_client_view_has_three_distinct_categories():
    """Verify that CollectionsClientView defines Mavzular, Franshizalar, and Xronologiyalar."""
    with open(CLIENT_VIEW, "r", encoding="utf-8") as f:
        content = f.read()

    assert "theme" in content
    assert "franchise" in content
    assert "chronology" in content
    assert "Xronologiyalar" in content
    assert "Franshizalar" in content
    assert "Mavzular" in content

def test_catalog_themes_includes_chronologies():
    """Verify that catalogThemes includes items categorized under chronology."""
    with open(CATALOG_THEMES, "r", encoding="utf-8") as f:
        content = f.read()

    assert '"chronology"' in content or "'chronology'" in content
