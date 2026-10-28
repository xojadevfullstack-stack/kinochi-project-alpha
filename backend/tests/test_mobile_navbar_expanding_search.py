import os
import re
import pytest

WEBSITE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "website")
)


def test_navbar_has_mobile_animated_expanding_search():
    """Asserts that Navbar.tsx implements an expanding mobile search with animated logo transition."""
    navbar_path = os.path.join(WEBSITE_DIR, "components", "Navbar.tsx")
    assert os.path.exists(navbar_path), "Navbar.tsx must exist"

    with open(navbar_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. State for mobile search
    assert "isMobileSearchOpen" in content, (
        "Navbar must contain isMobileSearchOpen state for mobile search toggle"
    )

    # 2. Dedicated mobile search button
    assert re.search(r"setIsMobileSearchOpen\s*\(\s*true\s*\)", content), (
        "Navbar must have a mobile search button that opens mobile search mode"
    )

    # 3. Logo smooth animated transition when search opens
    assert "isMobileSearchOpen" in content and "opacity-0" in content, (
        "Logo or navbar brand must animate with opacity-0 when mobile search is open"
    )

    # 4. Mobile search container with back/close action
    assert re.search(r"setIsMobileSearchOpen\s*\(\s*false\s*\)", content), (
        "Navbar must provide a back/close action that dismisses mobile search"
    )
    assert "arrow_back" in content or "close" in content, (
        "Mobile search bar must feature a back or close icon button"
    )

    # 5. LiveSearch embedded in mobile bar mode
    assert "isMobileBar" in content, (
        "LiveSearch must be rendered with isMobileBar in mobile search mode"
    )


def test_livesearch_supports_mobile_bar_and_autofocus():
    """Asserts that LiveSearch.tsx accepts isMobileBar, autoFocus, and onClose props."""
    live_search_path = os.path.join(WEBSITE_DIR, "components", "LiveSearch.tsx")
    assert os.path.exists(live_search_path), "LiveSearch.tsx must exist"

    with open(live_search_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Props interface
    assert "isMobileBar?:" in content, "LiveSearchProps must include isMobileBar?: boolean"
    assert "autoFocus?:" in content, "LiveSearchProps must include autoFocus?: boolean"
    assert "onClose?:" in content, "LiveSearchProps must include onClose?: () => void"

    # 2. Results popover fixed mobile positioning
    assert "isMobileBar" in content and ("fixed left-2 right-2" in content or "fixed inset-x-2" in content), (
        "LiveSearch must position dropdown fixed across mobile width when isMobileBar is active"
    )
