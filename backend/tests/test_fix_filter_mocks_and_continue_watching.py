from pathlib import Path


def test_movie_card_no_mocks():
    """F1-S14: MovieCard da mock Obuna, soxta yosh (6+), hardcoded O'zbekiston va tepasidagi mayda chiziq bo'lmasligi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    card_file = root_dir / "website" / "components" / "catalog" / "MovieCard.tsx"

    assert card_file.exists(), "MovieCard.tsx topilmadi"
    content = card_file.read_text(encoding="utf-8")

    # Obuna yozuvi olib tashlangan bo'lishi kerak
    assert "Obuna" not in content, "MovieCard da hali ham soxta 'Obuna' yozuvi mavjud"

    # Soxta 6+ yoki 16+ yosh ko'rsatmasi bo'lmasligi kerak
    assert '"6+"' not in content and "'6+'" not in content, "MovieCard da hali ham soxta '6+' yosh belgisi mavjud"
    assert '"16+"' not in content and "'16+'" not in content, "MovieCard da hali ham soxta '16+' yosh belgisi mavjud"

    # Hardcoded mamlakat (O'zbekiston) bo'lmasligi kerak
    assert "O'zbekiston" not in content, "MovieCard da hali ham hardcoded 'O\\'zbekiston' matni mavjud"

    # Soxta /TV platform reytingi bo'lmasligi kerak
    assert '"9.3"' not in content and "'9.3'" not in content, "MovieCard da soxta 9.3 reyting qoldig'i topildi"
    assert "/TV" not in content, "MovieCard da hali ham soxta '/TV' reyting badge mavjud"

    # Kartochka ustidagi mayda chiziq (stacked card effect) bo'lmasligi kerak
    assert "rounded-t-lg" not in content, "MovieCard ustidagi mayda chiziq (rounded-t-lg) olib tashlanmagan"


def test_unified_filter_bar_only_real_params():
    """F1-S14: UnifiedFilterBar da bazada yo'q parametrlar (subtitr, audiotrek, mamlakat, bepul pills) bo'lmasligi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    filter_file = root_dir / "website" / "components" / "catalog" / "UnifiedFilterBar.tsx"

    assert filter_file.exists(), "UnifiedFilterBar.tsx topilmadi"
    content = filter_file.read_text(encoding="utf-8")

    # Bazada yo'q parametrlar olib tashlangan bo'lishi kerak
    assert "Subtitr" not in content, "Filtrda hali ham bazada yo'q 'Subtitr' mavjud"
    assert "Audiotrek" not in content, "Filtrda hali ham bazada yo'q 'Audiotrek' mavjud"
    assert "Mamlakat" not in content, "Filtrda hali ham bazada yo'q 'Mamlakat' mavjud"
    assert "+ Bepul" not in content and "isFreeOnly" not in content, "Filtrda hali ham '+ Bepul' soxta pill mavjud"
    assert "+ O'zbek tilida" not in content and "isUzbekOnly" not in content, "Filtrda hali ham '+ O\\'zbek tilida' soxta pill mavjud"
    assert "+ Men uchun mavjud" not in content and "isAvailableOnly" not in content, "Filtrda hali ham '+ Men uchun mavjud' soxta pill mavjud"

    # Haqiqiy bazada mavjud parametrlar saqlangan bo'lishi kerak
    assert "Janr" in content
    assert "Bo'lim" in content
    assert "Yil" in content
    assert "Filtrlarni tozalash" in content


def test_navbar_z_index_above_filter():
    """F1-S14: Navbar z-index qiymati filtrdan yuqori bo'lishi va scroll qilinganda filtr uning ustiga chiqmasligi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    navbar_file = root_dir / "website" / "components" / "Navbar.tsx"
    catalog_page = root_dir / "website" / "app" / "catalog" / "page.tsx"

    nav_content = navbar_file.read_text(encoding="utf-8")
    cat_content = catalog_page.read_text(encoding="utf-8")

    # site-top-nav kamida z-50 bo'lishi lozim
    assert "site-top-nav" in nav_content
    assert "z-50" in nav_content or "z-[60]" in nav_content or "z-[100]" in nav_content

    # catalog dagi filter section z-40 bo'lmasligi kerak (navbar dan past bo'lishi shart)
    assert 'relative z-40' not in cat_content, "Catalog sahifasida filter section hali ham z-40 da qolgan"


def test_continue_watching_safe_urls():
    """F1-S14: ContinueWatching va TelegramWatchButton to'liq URL larni id/code sifatida saqlamasligi va 404 bermasligi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    cw_file = root_dir / "website" / "components" / "home" / "ContinueWatchingSection.tsx"
    btn_file = root_dir / "website" / "components" / "TelegramWatchButton.tsx"

    cw_content = cw_file.read_text(encoding="utf-8")
    btn_content = btn_file.read_text(encoding="utf-8")

    # TelegramWatchButton da seriesId va mediaId qo'llab-quvvatlanishi kerak
    assert "seriesId" in btn_content, "TelegramWatchButton da seriesId prop yo'q"

    # ContinueWatching da URL bo'lgan id lar tozalanib xavfsiz href yasalishi kerak
    assert "http" in cw_content or "startsWith" in cw_content or "cleanId" in cw_content


def test_movie_card_no_top_line():
    """F1-S14: MovieCard ustidagi mayda chiziq (h-1 bg-white/25 rounded-t-lg) olib tashlangan bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    card_file = root_dir / "website" / "components" / "catalog" / "MovieCard.tsx"
    card_content = card_file.read_text(encoding="utf-8")

    assert "rounded-t-lg" not in card_content, "MovieCard da keraksiz tepa chiziq (rounded-t-lg) qolib ketgan"
    assert "h-1 bg-white/25" not in card_content, "MovieCard da keraksiz oq chiziq qolib ketgan"
