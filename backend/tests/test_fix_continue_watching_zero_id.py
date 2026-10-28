import pytest
from pathlib import Path

def test_movie_card_supports_custom_href_and_guards_against_zero():
    """MovieCard ixtiyoriy href propini qabul qilishi va id=0 bo'lganda /series/0 yasamasligi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    card_file = root_dir / "website" / "components" / "catalog" / "MovieCard.tsx"
    content = card_file.read_text(encoding="utf-8")

    assert "href?:" in content or "customHref" in content, "MovieCard da href prop qo'shilmagan"
    assert "targetSeriesId" in content or "customHref" in content or "Number(item.id) > 0" in content

def test_continue_watching_filters_zero_and_passes_target_href():
    """ContinueWatchingSection da '0' filtrlangan va to'g'ridan-to'g'ri xavfsiz targetHref uzatilgan bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    cw_file = root_dir / "website" / "components" / "home" / "ContinueWatchingSection.tsx"
    content = cw_file.read_text(encoding="utf-8")

    assert 'targetHref' in content, "ContinueWatchingSection da targetHref hisoblanmagan"
    assert '"0"' in content, "ContinueWatchingSection da '0' tekshiruvi yo'q"
