from pathlib import Path


def test_home_page_uses_movie_card_component():
    """F1-S11: Bosh sahifadagi barcha kartochkalar yangi MovieCard komponentidan foydalanishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    page_file = root_dir / "website" / "app" / "page.tsx"

    assert page_file.exists(), "website/app/page.tsx topilmadi"
    content = page_file.read_text(encoding="utf-8")

    assert "import MovieCard from" in content, "page.tsx da MovieCard import qilinmagan"
    assert "<MovieCard" in content, "page.tsx da <MovieCard /> chaqirilmagan"
    # Eski ichki matnli kartochka qoldiqlari bo'lmasligi kerak
    assert "line-clamp-2 drop-shadow-md" not in content, "page.tsx da eski inline kartochka qoldiqlari topildi"


def test_marquee_section_aligned_to_container_boundaries():
    """F1-S11: MediaMarqueeSection chegaralari max-w-container-max ga moslangan bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    marquee_file = root_dir / "website" / "components" / "home" / "MediaMarqueeSection.tsx"

    assert marquee_file.exists(), "MediaMarqueeSection.tsx topilmadi"
    content = marquee_file.read_text(encoding="utf-8")

    # max-w-full butun ekranga yoyilib ketishi o'rniga max-w-container-max konteyneri bo'lishi lozim
    assert "max-w-container-max mx-auto px-gutter my-12" in content or "max-w-container-max" in content
    assert "max-w-full mx-auto my-12" not in content, "MediaMarqueeSection da hali ham max-w-full qolgan"
