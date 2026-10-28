import os
import re
import pytest

WEBSITE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "website")
)


def test_catalog_filter_position_and_conditional_hide():
    """Asserts that UnifiedFilterBar is placed between search header and 6 categories,
    and 6 categories are hidden when filter is active."""
    catalog_path = os.path.join(WEBSITE_DIR, "app", "catalog", "page.tsx")
    assert os.path.exists(catalog_path), "catalog/page.tsx must exist"

    with open(catalog_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Filter bar must appear BEFORE the 6 category cards
    filter_pos = content.find("<UnifiedFilterBar")
    categories_pos = content.find("CATALOG_CATEGORIES.map")
    assert filter_pos != -1, "UnifiedFilterBar must be in catalog/page.tsx"
    assert categories_pos != -1, "CATALOG_CATEGORIES.map must be in catalog/page.tsx"
    assert filter_pos < categories_pos, (
        f"UnifiedFilterBar (pos {filter_pos}) must appear BEFORE 6 category cards (pos {categories_pos})"
    )

    # 2. 6 category cards must be conditionally rendered only when no filter is active
    assert "!hasFilterActive" in content, (
        "6 category cards section must be conditioned on !hasFilterActive"
    )
