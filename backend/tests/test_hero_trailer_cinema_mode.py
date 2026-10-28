import os

def test_hero_trailer_backdrop_supports_inactivity_cinema_mode():
    path = os.path.join("website", "components", "media", "HeroTrailerBackdrop.tsx")
    assert os.path.exists(path), f"{path} must exist"
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Must support children prop
    assert "children" in content, "HeroTrailerBackdrop must accept children"
    # Must have dimmed / ambient cinema mode state
    assert "isDimmed" in content or "isCinemaMode" in content, "Must have dimmed / cinema mode state"
    assert "scroll" in content.lower(), "Must listen to scroll event to restore details"
    assert "setTimeout" in content or "timer" in content.lower(), "Must use inactivity timer"
    # Must provide semi-transparency for second-tier details
    assert "opacity-25" in content or "opacity-20" in content or "opacity-30" in content, \
        "Details must be semi-transparent when dimmed"

def test_series_and_movie_pages_wrap_content_in_hero_backdrop():
    series_path = os.path.join("website", "app", "series", "[id]", "page.tsx")
    movie_path = os.path.join("website", "app", "movie", "[code]", "page.tsx")
    
    for path, name in [(series_path, "series"), (movie_path, "movie")]:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        assert "<HeroTrailerBackdrop" in content, f"{name} page must use HeroTrailerBackdrop"
        assert "</HeroTrailerBackdrop>" in content, f"{name} page must wrap content inside HeroTrailerBackdrop"
