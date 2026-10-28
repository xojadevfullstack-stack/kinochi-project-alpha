import pytest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

def test_navbar_has_accessible_hamburger_button_and_responsive_sidebar():
    navbar_path = REPO_ROOT / "website" / "components" / "Navbar.tsx"
    assert navbar_path.exists(), "Navbar.tsx must exist"
    content = navbar_path.read_text(encoding="utf-8")

    # 1. Hamburger menu button must exist in top navbar
    assert 'aria-label="Menyuni ochish"' in content
    assert 'material-symbols-outlined' in content
    assert 'menu' in content

    # 2. Sidebar aside container must NOT be hard-hidden below xl
    assert "hidden xl:flex" not in content
    assert "flex fixed top-0 left-0 bottom-0 w-72 z-[60]" in content

    # 3. Backdrop overlay must be responsive (not hidden below xl)
    assert "hidden xl:block fixed inset-0 z-40 bg-black/40" not in content
    assert "fixed inset-0 z-50 bg-black/60" in content

def test_details_pages_pass_initial_credits_for_zero_skeleton_ssr():
    series_page = REPO_ROOT / "website" / "app" / "series" / "[id]" / "page.tsx"
    movie_page = REPO_ROOT / "website" / "app" / "movie" / "[code]" / "page.tsx"

    assert series_page.exists()
    assert movie_page.exists()

    series_content = series_page.read_text(encoding="utf-8")
    movie_content = movie_page.read_text(encoding="utf-8")

    # Series page passes initial credits from server
    assert "creditsData = await fetchApi(`/series/${series.id}/credits`)" in series_content
    assert "initialCredits={creditsData?.items}" in series_content
    assert "initialDetails={creditsData?.details}" in series_content

    # Movie page passes initial credits from server
    assert "creditsData = await fetchApi(`/movies/${movie.code || movie.id}/credits`)" in movie_content
    assert "initialCredits={creditsData?.items}" in movie_content
    assert "initialDetails={creditsData?.details}" in movie_content
