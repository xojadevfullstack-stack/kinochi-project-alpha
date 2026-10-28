from pathlib import Path


def test_media_marquee_section_exists_and_contract():
    """F1-S07: website/components/home/MediaMarqueeSection.tsx mavjudligi va shartnomasi."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    marquee_file = root_dir / "website" / "components" / "home" / "MediaMarqueeSection.tsx"

    assert marquee_file.exists(), "MediaMarqueeSection.tsx topilmadi"
    content = marquee_file.read_text(encoding="utf-8")

    assert "animate-marquee" in content, "Cheksiz aylanuvchi marquee animatsiyasi topilmadi"
    assert "rounded-2xl" in content, "Kartochkalar uchun rounded-2xl topilmadi"
    assert "Kinolar va seriallar" in content or "Telekanallar" in content or "Premyeralar" in content


def test_media_marquee_mounted_in_home_page():
    """F1-S07: website/app/page.tsx da MediaMarqueeSection chaqirilgan bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    page_file = root_dir / "website" / "app" / "page.tsx"

    assert page_file.exists(), "website/app/page.tsx topilmadi"
    content = page_file.read_text(encoding="utf-8")

    assert "MediaMarqueeSection" in content, "page.tsx da MediaMarqueeSection topilmadi"
    assert "<MediaMarqueeSection" in content, "page.tsx da <MediaMarqueeSection /> komponenti chaqirilmagan"
