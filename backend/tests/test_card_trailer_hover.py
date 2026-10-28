import os

def test_catalog_item_schema_has_trailer_url():
    path = os.path.join("website", "lib", "api", "catalog.ts")
    assert os.path.exists(path), f"{path} must exist"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "trailer_url" in content, "CatalogItem must have trailer_url property"

def test_movie_card_supports_trailer_hover_and_mobile_touch():
    path = os.path.join("website", "components", "catalog", "MovieCard.tsx")
    assert os.path.exists(path), f"{path} must exist"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "use client" in content, "MovieCard must be a client component for hover preview"
    assert "trailer_url" in content or "trailerUrl" in content, "MovieCard must check trailer_url"
    assert "onMouseEnter" in content and "onMouseLeave" in content, "MovieCard must support desktop hover"
    assert "onTouchStart" in content or "touch" in content.lower(), "MovieCard must support mobile touch/hold"
    assert "mute" in content.lower() or "muted" in content.lower(), "Trailer preview must be muted"

def test_hero_trailer_backdrop_scroll_threshold_and_touch():
    path = os.path.join("website", "components", "media", "HeroTrailerBackdrop.tsx")
    assert os.path.exists(path), f"{path} must exist"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "touchmove" in content or "touchstart" in content, "Must handle mobile touch scroll"
    assert "scrollY" in content, "Must check scroll position threshold"
