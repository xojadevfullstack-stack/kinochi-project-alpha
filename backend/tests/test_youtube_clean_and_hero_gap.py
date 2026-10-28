import os

def test_movie_card_crops_youtube_ui_and_fits_mobile():
    path = os.path.join("website", "components", "catalog", "MovieCard.tsx")
    assert os.path.exists(path), f"{path} must exist"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # Must crop out YouTube top header (channel avatar and title)
    assert "w-[280%]" in content or "w-[300%]" in content or "scale-150" in content or "scale-[1.5]" in content or "scale-[2" in content or "w-[2" in content, \
        "MovieCard must crop YouTube top bar by sizing container beyond card bounds"
    assert "disablekb=1" in content or "controls=0" in content, "Must disable YouTube controls"

def test_hero_trailer_backdrop_glues_to_top_edge():
    path = os.path.join("website", "components", "media", "HeroTrailerBackdrop.tsx")
    assert os.path.exists(path), f"{path} must exist"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # Must ensure zero gap at top
    assert "-top-" in content or "top-0" in content, "HeroTrailerBackdrop must anchor or overlap top edge to eliminate black gap"
    assert "scale-1" in content or "scale-[1" in content or "scale-12" in content, "Must scale video to crop YouTube elements on mobile and desktop"
