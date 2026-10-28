import pytest
from pathlib import Path

def test_tmdb_client_has_get_credits():
    """F1-S16: tmdb_client da get_credits metodi mavjud bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    tmdb_file = root_dir / "backend" / "app" / "infrastructure" / "external" / "tmdb_client.py"
    content = tmdb_file.read_text(encoding="utf-8")

    assert "def get_credits" in content, "tmdb_client da get_credits metodi aniqlanmagan"
    assert "credits" in content

def test_movie_and_series_credits_api_endpoints():
    """F1-S16: movies va series API larida /credits endpointlari mavjud bo'lishi kerak."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    movies_api = root_dir / "backend" / "app" / "api" / "v1" / "movies.py"
    series_api = root_dir / "backend" / "app" / "api" / "v1" / "series.py"

    m_content = movies_api.read_text(encoding="utf-8")
    s_content = series_api.read_text(encoding="utf-8")

    assert "/credits" in m_content, "movies API da /credits endpointi yo'q"
    assert "/credits" in s_content, "series API da /credits endpointi yo'q"

def test_cast_crew_component_and_integration():
    """F1-S16: Suratga olish guruhi komponenti va uning tafsilot sahifalariga ulanishi."""
    root_dir = Path(__file__).resolve().parent.parent.parent
    component_file = root_dir / "website" / "components" / "media" / "CastCrewSection.tsx"
    movie_page = root_dir / "website" / "app" / "movie" / "[code]" / "page.tsx"
    series_page = root_dir / "website" / "app" / "series" / "[id]" / "page.tsx"

    assert component_file.exists(), "CastCrewSection.tsx komponenti mavjud emas"
    comp_content = component_file.read_text(encoding="utf-8")
    assert "Suratga olish guruhi" in comp_content, "Komponentda 'Suratga olish guruhi' sarlavhasi yo'q"

    assert "CastCrewSection" in movie_page.read_text(encoding="utf-8"), "Movie tafsilot sahifasida CastCrewSection yo'q"
    assert "CastCrewSection" in series_page.read_text(encoding="utf-8"), "Series tafsilot sahifasida CastCrewSection yo'q"
