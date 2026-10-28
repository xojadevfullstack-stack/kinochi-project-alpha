import os
import pytest

WEBSITE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "website")
)


def test_catalog_and_six_dedicated_pages():
    """Asserts that all 6 dedicated pages exist and catalog routes to them."""
    # 1. 6 Dedicated page files must exist
    expected_pages = [
        ("top100", "Top 100"),
        ("movies", "Kinolar"),
        ("series", "Seriallar"),
        ("doramas", "Doramalar"),
        ("anime", "Anime"),
        ("cartoons", "Multfilmlar"),
    ]

    for slug, title in expected_pages:
        page_path = os.path.join(WEBSITE_DIR, "app", slug, "page.tsx")
        assert os.path.exists(page_path), f"Dedicated page website/app/{slug}/page.tsx must exist"

    # 2. Catalog page must link to all 6 dedicated pages
    catalog_path = os.path.join(WEBSITE_DIR, "app", "catalog", "page.tsx")
    assert os.path.exists(catalog_path), "catalog/page.tsx must exist"
    with open(catalog_path, "r", encoding="utf-8") as f:
        catalog_content = f.read()

    assert "/top100" in catalog_content, "Catalog must link to /top100"
    assert "/movies" in catalog_content, "Catalog must link to /movies"
    assert "/series" in catalog_content, "Catalog must link to /series"
    assert "/doramas" in catalog_content, "Catalog must link to /doramas"
    assert "/anime" in catalog_content, "Catalog must link to /anime"
    assert "/cartoons" in catalog_content, "Catalog must link to /cartoons"
    assert "top 100" in catalog_content.lower(), "Catalog must display 'Top 100'"
