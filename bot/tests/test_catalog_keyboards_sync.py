import pytest
from keyboards.inline import get_catalog_categories_inline


def test_catalog_categories_deduplication():
    """Verify that pages titled 'Kino' and 'Serial' or slug 'movie'/'series' do not duplicate top-level buttons."""
    mock_pages = [
        {"id": 1, "title": "Anime", "slug": "anime", "is_active": True},
        {"id": 5, "title": "Doramalar", "slug": "Dorama", "is_active": True},
        {"id": 8, "title": "Multfilm", "slug": "Cartoon", "is_active": True},
        {"id": 9, "title": "Kino", "slug": "movie", "is_active": True},
        {"id": 18, "title": "Serial", "slug": "series", "is_active": True},
    ]

    markup = get_catalog_categories_inline(mock_pages)
    
    # Flatten all buttons
    all_buttons = [btn for row in markup.inline_keyboard for btn in row]
    button_texts = [btn.text for btn in all_buttons]

    # Must contain main categories
    assert any("Kinolar" in t for t in button_texts)
    assert any("Seriallar" in t for t in button_texts)
    assert any("Franshizalar & To'plamlar" in t for t in button_texts)
    assert any("Anime" in t for t in button_texts)
    assert any("Doramalar" in t for t in button_texts)
    assert any("Multfilm" in t for t in button_texts)

    # MUST NOT contain duplicate "Kino" or "Serial" page buttons
    assert not any(t.strip() in ("📁 Kino", "📂 Kino") for t in button_texts)
    assert not any(t.strip() in ("📁 Serial", "📂 Serial") for t in button_texts)

    # Franshizalar should be on its own row for optimal layout
    row_with_franchise = next(row for row in markup.inline_keyboard if any("Franshizalar" in btn.text for btn in row))
    assert len(row_with_franchise) == 1
