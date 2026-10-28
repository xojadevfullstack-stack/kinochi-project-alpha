from pathlib import Path


def test_compact_premyeralar_title_for_mobile():
    """F1-S09: Mobilda joy tejash uchun 'Eng so'nggi premyeralar va yangiliklar' ixchamlashtirilgan bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    page_file = root_dir / "website" / "app" / "page.tsx"

    assert page_file.exists(), "page.tsx topilmadi"
    content = page_file.read_text(encoding="utf-8")

    # Juda uzun bo'lgan sarlavha olib tashlanishi kerak
    assert "Eng so'nggi premyeralar va yangiliklar</span>" not in content, "Uzun 'Eng so'nggi premyeralar va yangiliklar' sarlavhasi hali ham mavjud"
    assert "Yangi premyeralar" in content or "Premyeralar va yangiliklar" in content


def test_marquee_cards_scaled_up_for_mobile():
    """F1-S09: Mobilda juda mayda bo'lib qolmasligi uchun kartochkalar o'lchami kattalashtirilgan bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    marquee_file = root_dir / "website" / "components" / "home" / "MediaMarqueeSection.tsx"

    assert marquee_file.exists(), "MediaMarqueeSection.tsx topilmadi"
    content = marquee_file.read_text(encoding="utf-8")

    # w-20 h-20 mayda o'lcham o'rniga kattaroq (kamida w-28 h-28) bo'lishi lozim
    assert "w-20" not in content, "MediaMarqueeSection da mayda w-20 o'lchami topildi"
    assert "w-28" in content, "MediaMarqueeSection da w-28 o'lchami topilmadi"
