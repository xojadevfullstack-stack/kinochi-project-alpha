import pytest
from scraper.duplicate_checker import to_slug, to_stem_slug

def test_cyrillic_to_slug_transliteration():
    """F-016: Kirill yozuvidagi sarlavhalar tozalab tashlanmasdan to'g'ri slug qilinishi kerak."""
    assert to_slug("Ўргимчак одам") == "orgimchakodam"
    assert to_slug("Қашқирлар макони") == "qashqirlarmakoni"
    assert to_slug("Иблислар қотили") == "iblislarqotili"
    assert to_slug("Чол ва денгиз") == "cholvadengiz"
    assert to_slug("Человек-паук") == "chelovekpauk"

def test_cyrillic_to_stem_slug():
    """F-016: Kirill yozuvidagi sarlavhalar o'zak slugida ham bo'sh qaytmasligi kerak."""
    stem = to_stem_slug("Ўргимчак одам")
    assert stem != "", "to_stem_slug kirillcha matn uchun bo'sh satr qaytarmasligi kerak"
    assert "orgimchak" in stem
