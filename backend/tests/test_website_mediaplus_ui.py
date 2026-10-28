from pathlib import Path


def test_no_hardcoded_rating_mock_in_home_page():
    """F1-S02: website/app/page.tsx da soxta '8.5' reyting mocki bo'lmasligi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    page_file = root_dir / "website" / "app" / "page.tsx"
    assert page_file.exists(), "website/app/page.tsx topilmadi"
    content = page_file.read_text(encoding="utf-8")

    assert '"8.5"' not in content, "website/app/page.tsx da '8.5' soxta reyting mocki topildi"


def test_code_badge_not_rendered_on_clean_posters():
    """F1-S08: Foydalanuvchi talabi bilan kartochkalar ustidan #{item.code} badgesi olib tashlandi."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    page_file = root_dir / "website" / "app" / "page.tsx"
    card_file = root_dir / "website" / "components" / "catalog" / "MovieCard.tsx"

    assert page_file.exists()
    assert card_file.exists()

    page_content = page_file.read_text(encoding="utf-8")
    card_content = card_file.read_text(encoding="utf-8")

    assert "#{item.code}" not in page_content, "website/app/page.tsx da #{item.code} badgesi qolgan"
    assert "#{item.code}" not in card_content, "website/components/catalog/MovieCard.tsx da #{item.code} badgesi qolgan"
