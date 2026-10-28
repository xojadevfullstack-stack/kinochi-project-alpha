import os
import pytest

WEBSITE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "website")
)


def test_catalog_page_has_six_category_cards_hub():
    """Asserts that catalog/page.tsx features 6 primary category cards and clean structure."""
    catalog_path = os.path.join(WEBSITE_DIR, "app", "catalog", "page.tsx")
    assert os.path.exists(catalog_path), "catalog/page.tsx must exist"

    with open(catalog_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Old cluttered themes / Asilmedia deck must be completely purged from catalog
    assert "CURATED_CATALOG_THEMES" not in content, (
        "Old themes deck (CURATED_CATALOG_THEMES) must be removed from catalog/page.tsx"
    )
    assert "ThemedCollectionCard" not in content, (
        "ThemedCollectionCard must not be rendered in catalog/page.tsx"
    )

    # 2. Must feature the 6 dedicated category routes
    assert "/top100" in content, "Catalog must contain Top 100 dedicated route"
    assert "/movies" in content, "Catalog must contain Kinolar dedicated route"
    assert "/series" in content, "Catalog must contain Seriallar dedicated route"
    assert "/doramas" in content, "Catalog must contain Doramalar dedicated route"
    assert "/anime" in content, "Catalog must contain Anime dedicated route"
    assert "/cartoons" in content, "Catalog must contain Multfilmlar dedicated route"

    # 3. Must display the 6 card titles
    for name in ["Top 100", "Kino", "Serial", "Dorama", "Anime", "Multfilm"]:
        assert name.lower() in content.lower(), f"Catalog must feature '{name}' category"
