from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_marquee_no_mock_fhd_hd_badges():
    """MediaMarqueeSection da mock FHD / HD yorliqlari bo'lmasligi kerak."""
    content = (ROOT / "website" / "components" / "home" / "MediaMarqueeSection.tsx").read_text(encoding="utf-8")
    assert "qualityBadge" not in content
    assert '"FHD"' not in content
    assert '"HD"' not in content


def test_marquee_title_has_blur_and_lighter_weight():
    """MediaMarqueeSection da sarlavha foni blur bilan va matn qalinligi biroz yengil (font-medium) bo'lishi kerak."""
    content = (ROOT / "website" / "components" / "home" / "MediaMarqueeSection.tsx").read_text(encoding="utf-8")
    assert "backdrop-blur" in content
    assert "font-medium" in content
    # Eski qalin font-bold sarlavhada bo'lmasligi kerak
    assert "font-bold truncate leading-tight" not in content
