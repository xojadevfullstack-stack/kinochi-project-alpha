import pytest
from pathlib import Path

def test_movie_card_has_unified_single_rating_template():
    """F1-S17: MovieCard da barcha filmlar uchun yagona IMDb reyting shabloni bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    card_file = root_dir / "website" / "components" / "catalog" / "MovieCard.tsx"
    content = card_file.read_text(encoding="utf-8")

    assert "displayRating" in content, "MovieCard da yagona displayRating hisoblanmagan"
    assert "bg-[#f5c518]" in content, "IMDb badge yo'q"

def test_continue_watching_auto_enriches_year_and_rating():
    """F1-S17 / F1-S20: ContinueWatchingSection yildan yoki reytingdan mahrum bo'lgan (Chernobil kabi) eski kartochkalarni auto-enrich qilishi va saqlashi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    cw_file = root_dir / "website" / "components" / "home" / "ContinueWatchingSection.tsx"
    content = cw_file.read_text(encoding="utf-8")

    assert "release_year" in content, "ContinueWatchingSection da release_year qamrab olinmagan"
    assert "imdb_rating" in content, "ContinueWatchingSection da imdb_rating qamrab olinmagan"
    assert "episodes/code" in content, "Episode code fallback enrich yo'q"
    assert "mediaplus_continue_watching" in content, "Enriched holatni localStorage ga saqlash yo'q"

def test_telegram_watch_button_persists_full_meta():
    """F1-S17: TelegramWatchButton releaseYear va imdbRating ni qabul qilib saqlashi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    btn_file = root_dir / "website" / "components" / "TelegramWatchButton.tsx"
    content = btn_file.read_text(encoding="utf-8")

    assert "releaseYear" in content, "TelegramWatchButton da releaseYear prop yo'q"
    assert "imdbRating" in content, "TelegramWatchButton da imdbRating prop yo'q"

def test_history_grid_and_api_includes_meta():
    """F1-S20: HistoryGrid va users.py /me/history reyting va yil parametrlarini taqdim etishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    hg_file = root_dir / "website" / "components" / "history" / "HistoryGrid.tsx"
    hg_content = hg_file.read_text(encoding="utf-8")
    assert "imdb_rating: item.movie.imdb_rating" in hg_content
    assert "imdb_rating: item.episode.imdb_rating" in hg_content

    users_file = root_dir / "backend" / "app" / "api" / "v1" / "users.py"
    users_content = users_file.read_text(encoding="utf-8")
    assert '"release_year": record.movie.release_year' in users_content
    assert '"imdb_rating": record.movie.imdb_rating' in users_content
