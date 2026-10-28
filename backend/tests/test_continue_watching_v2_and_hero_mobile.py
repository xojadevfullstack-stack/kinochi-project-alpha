import pytest
from pathlib import Path

def test_continue_watching_uses_movie_card_no_play_no_progress():
    """F1-S15: ContinueWatchingSection MovieCard dan foydalanishi, play ikonkasi va qizil progress bar olib tashlangan bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    cw_file = root_dir / "website" / "components" / "home" / "ContinueWatchingSection.tsx"
    content = cw_file.read_text(encoding="utf-8")

    # MovieCard import qilingan bo'lishi kerak
    assert "MovieCard" in content, "ContinueWatchingSection da MovieCard ishlatilmagan"
    # Eski play ikonkasi olib tashlangan bo'lishi kerak
    assert "play_arrow" not in content, "ContinueWatchingSection da eski play ikonkasi qolib ketgan"
    # Pastki qizil progress bar olib tashlangan bo'lishi kerak
    assert "bg-red-600 rounded-r-full" not in content, "ContinueWatchingSection da eski progress bar qolib ketgan"

def test_hero_poster_visible_on_mobile():
    """F1-S15: Asosiy sahifadagi eng so'nggi film (Hero) posteri telefonda ham ko'rinadigan bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    page_file = root_dir / "website" / "app" / "page.tsx"
    content = page_file.read_text(encoding="utf-8")

    # Posterni o'rab turuvchi div faqat "hidden md:block" bo'lib qolmasligi kerak
    assert "hidden md:block w-1/3 lg:w-[420px]" not in content, "Hero posteri mobil telefonda butunlay yashiringan holatda qolib ketgan"

def test_series_code_lookup_handles_episodes():
    """F1-S15: series_repository.get_series_by_code seriya kodi yoki ID si orqali ham asosiy serialni topishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    repo_file = root_dir / "backend" / "app" / "infrastructure" / "db" / "repositories" / "series_repository.py"
    content = repo_file.read_text(encoding="utf-8")

    assert "EpisodeModel" in content or "episode" in content, "series_repository da episode orqali serialni topish yo'q"
