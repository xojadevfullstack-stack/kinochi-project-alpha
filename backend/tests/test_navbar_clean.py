from pathlib import Path


def test_navbar_cleaned_from_dead_and_redundant_menus():
    """F1-S03: Navbar.tsx dan chala/o'lik havolalar va ortiqcha dropdownlar tozalangan bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    navbar_file = root_dir / "website" / "components" / "Navbar.tsx"
    assert navbar_file.exists(), "Navbar.tsx topilmadi"
    content = navbar_file.read_text(encoding="utf-8")

    # 1. Dead/broken links must not exist
    assert "/catalog?category=treyler" not in content, "Treylerlar chala havolasi topildi"
    assert 'href="/tv"' not in content, "Onlayn TV chala havolasi topildi"
    assert "setBolimlarOpen" not in content, "Ortiqcha bolimlarOpen dropdown holati topildi"
    assert "setKolleksiyaOpen" not in content, "Ortiqcha kolleksiyaOpen dropdown holati topildi"

    # 2. Clean main links must exist
    assert 'href="/catalog"' in content
    assert 'href="/series"' in content
    assert 'href="/collections"' in content
    assert 'href="/actors"' in content
    assert 'href="/requests"' in content
