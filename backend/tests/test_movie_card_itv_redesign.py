from pathlib import Path


def test_movie_card_split_layout_and_ratings():
    """F1-S06 & F1-S14: MovieCard split dizayni haqiqiy ma'lumotlar bilan ishlashi kerak (mocklarsiz)."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    card_file = root_dir / "website" / "components" / "catalog" / "MovieCard.tsx"

    assert card_file.exists(), "MovieCard.tsx topilmadi"
    content = card_file.read_text(encoding="utf-8")

    # 1. Poster ostidagi alohida sarlavha (soxta Obuna yozuvisiz)
    assert "Obuna" not in content, "Soxta Obuna yozuvi MovieCard da qolmasligi kerak"
    assert "rounded-2xl" in content, "Poster uchun rounded-2xl klassi topilmadi"

    # 2. Haqiqiy IMDb reyting bloki
    assert "IMDb" in content, "IMDb reyting bloki topilmadi"

    # 3. Soxta yosh (6+, 16+) bo'lmasligi, faqat haqiqiy 18+ bo'lishi kerak
    assert "6+" not in content and "16+" not in content
    assert "18+" in content

    # 4. Foydalanuvchi talabi bilan kartochkadan #{item.code} olib tashlandi
    assert "#{item.code}" not in content, "Telegram bot kodi #{item.code} kartochkadan o'chirilmadi"

    # 5. Cinematic Red standarti: MovieCard hoverda sarlavha sariq (rating-gold) bo'lmasligi, primary red bo'lishi shart
    assert "group-hover:text-rating-gold" not in content, "MovieCard sarlavhasi hoverda sariq (rating-gold) bo'lmasligi shart"
    assert "group-hover:text-primary" in content, "MovieCard sarlavhasi hoverda group-hover:text-primary bo'lishi shart"
