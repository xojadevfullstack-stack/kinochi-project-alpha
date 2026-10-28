from pathlib import Path


def test_premieres_page_exists():
    """F1-S10: website/app/premieres/page.tsx alohida premyeralar sahifasi mavjud bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    premieres_page = root_dir / "website" / "app" / "premieres" / "page.tsx"

    assert premieres_page.exists(), "app/premieres/page.tsx topilmadi"
    content = premieres_page.read_text(encoding="utf-8")
    assert "Premyeralar" in content, "Premyeralar sarlavhasi topilmadi"


def test_bottom_nav_and_navbar_link_to_premieres():
    """F1-S10: BottomNav va Navbar dagi Premyera havolasi /premieres ga yo'naltirilishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    bottom_nav = root_dir / "website" / "components" / "BottomNav.tsx"
    navbar = root_dir / "website" / "components" / "Navbar.tsx"

    assert bottom_nav.exists()
    assert navbar.exists()

    b_content = bottom_nav.read_text(encoding="utf-8")
    n_content = navbar.read_text(encoding="utf-8")

    assert '"/premieres"' in b_content, "BottomNav da /premieres havolasi topilmadi"
    assert '"/premieres"' in n_content, "Navbar da /premieres havolasi topilmadi"


def test_catalog_grid_is_3_columns_on_mobile():
    """F1-S10: CatalogGrid mobilda 2 emas, 3 qator (grid-cols-3) bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    grid_file = root_dir / "website" / "components" / "catalog" / "CatalogGrid.tsx"

    assert grid_file.exists()
    content = grid_file.read_text(encoding="utf-8")

    assert "grid-cols-3" in content, "CatalogGrid da grid-cols-3 topilmadi"
    assert "grid grid-cols-2" not in content, "CatalogGrid da hali ham mobil uchun grid-cols-2 qolgan"
