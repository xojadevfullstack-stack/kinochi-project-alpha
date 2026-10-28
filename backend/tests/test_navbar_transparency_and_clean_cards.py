from pathlib import Path


def test_navbar_transparency_glassmorphic():
    """F1-S08: Navbar shaffof (translucent) glassmorphic dizaynga ega bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    navbar_file = root_dir / "website" / "components" / "Navbar.tsx"

    assert navbar_file.exists(), "Navbar.tsx topilmadi"
    content = navbar_file.read_text(encoding="utf-8")

    # Navbar background-obsidian/95 to'liq qora o'rniga shaffofroq (masalan, bg-black/40 yoki bg-black/20) bo'lishi lozim
    assert "backdrop-blur" in content
    assert "bg-black/40" in content or "bg-black/30" in content or "bg-black/20" in content or "bg-background-obsidian/40" in content


def test_code_and_serial_badges_removed_from_cards():
    """F1-S08: Foydalanuvchi talabiga ko'ra #{item.code} va SERIAL yozuvlari kartochkalardan olib tashlanishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    card_file = root_dir / "website" / "components" / "catalog" / "MovieCard.tsx"
    page_file = root_dir / "website" / "app" / "page.tsx"

    assert card_file.exists()
    assert page_file.exists()

    card_content = card_file.read_text(encoding="utf-8")
    page_content = page_file.read_text(encoding="utf-8")

    # Kartochkalarda #{item.code} va SERIAL nishonlari bo'lmasligi kerak
    assert "#{item.code}" not in card_content, "MovieCard da hali ham #{item.code} nishoni mavjud"
    assert "SERIAL" not in card_content, "MovieCard da hali ham SERIAL nishoni mavjud"
    assert "#{item.code}" not in page_content, "page.tsx kartochkalarida hali ham #{item.code} nishoni mavjud"
