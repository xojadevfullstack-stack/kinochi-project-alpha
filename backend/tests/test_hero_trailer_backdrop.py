import os
import re

def test_hero_trailer_backdrop_component_exists():
    path = os.path.join("website", "components", "media", "HeroTrailerBackdrop.tsx")
    assert os.path.exists(path), f"HeroTrailerBackdrop component must exist at {path}"
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Assert key capabilities
    assert "use client" in content, "Must be a client component"
    assert "trailerUrl" in content, "Must accept trailerUrl prop"
    assert "posterUrl" in content, "Must accept posterUrl prop"
    assert "mute" in content.lower() or "muted" in content.lower(), "Must handle muted background playback"
    assert "AdultHeroBackground" in content, "Must fallback to AdultHeroBackground for instant LCP"

def test_series_details_page_uses_hero_trailer_and_removes_bulky_section():
    series_page = os.path.join("website", "app", "series", "[id]", "page.tsx")
    assert os.path.exists(series_page), f"File {series_page} must exist"
    
    with open(series_page, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "HeroTrailerBackdrop" in content, "series/[id]/page.tsx must import and use HeroTrailerBackdrop"
    # Ensure bulky standalone trailer section was removed
    assert '<h2 className="font-headline-md text-headline-md text-text-primary mb-stack-md flex items-center gap-3">' not in content, \
        "Bulky standalone 'Treyler' section must be removed from series details"
    assert 'bg-rating-gold rounded-full block' not in content, \
        "Forbidden yellow/gold bar must not be used for trailer section"

def test_movie_details_page_uses_hero_trailer_and_removes_bulky_section():
    movie_page = os.path.join("website", "app", "movie", "[code]", "page.tsx")
    assert os.path.exists(movie_page), f"File {movie_page} must exist"
    
    with open(movie_page, "r", encoding="utf-8") as f:
        content = f.read()
        
    assert "HeroTrailerBackdrop" in content, "movie/[code]/page.tsx must import and use HeroTrailerBackdrop"
    # Ensure bulky standalone trailer section was removed
    assert '<h2 className="font-headline-md text-headline-md text-text-primary mb-stack-md">Treyler</h2>' not in content, \
        "Bulky standalone 'Treyler' section must be removed from movie details"
