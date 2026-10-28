import pytest
import os
import re

WEBSITE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "website"))
SERIES_PAGE = os.path.join(WEBSITE_DIR, "app", "series", "[id]", "page.tsx")
SEASON_COMPONENT = os.path.join(WEBSITE_DIR, "components", "media", "SeasonEpisodesSection.tsx")

def test_season_episodes_section_file_exists():
    """Verify that SeasonEpisodesSection component exists."""
    assert os.path.exists(SEASON_COMPONENT), f"Missing {SEASON_COMPONENT}"

def test_season_episodes_section_features():
    """Verify season tabs, compact responsive grid, and absence of bulky full-page poster on mobile."""
    with open(SEASON_COMPONENT, "r", encoding="utf-8") as f:
        content = f.read()

    # Must be interactive client component
    assert '"use client"' in content or "'use client'" in content
    
    # Must support season tabs switching
    assert "activeSeason" in content or "selectedSeason" in content or "currentSeason" in content
    
    # Must use compact responsive grid (cols-2 or cols-3 on mobile instead of giant 1-col full screen)
    assert "grid-cols-2" in content or "grid-cols-3" in content
    
    # Must integrate TelegramWatchButton
    assert "TelegramWatchButton" in content
    assert "episode.code" in content or "episode_number" in content

def test_series_page_integrates_season_episodes_section():
    """Verify series/[id]/page.tsx delegates to SeasonEpisodesSection."""
    with open(SERIES_PAGE, "r", encoding="utf-8") as f:
        content = f.read()

    assert "SeasonEpisodesSection" in content
    assert "<SeasonEpisodesSection" in content

def test_season_episodes_section_cinematic_red_standard():
    """Verify that SeasonEpisodesSection uses Primary Red for active tabs and hover, never rating-gold."""
    with open(SEASON_COMPONENT, "r", encoding="utf-8") as f:
        content = f.read()

    assert "bg-rating-gold text-black" not in content, "Active season tab must not use yellow bg-rating-gold"
    assert "hover:border-rating-gold" not in content, "Episode hover must not use yellow border-rating-gold"
    assert "group-hover:text-rating-gold" not in content, "Episode hover must not use group-hover:text-rating-gold"
    assert "bg-primary" in content, "Active season tab must use bg-primary"

def test_season_episodes_section_bot_link_format():
    """Verify that episode links format deep link with ep_ prefix and robust botUsername fallback."""
    with open(SEASON_COMPONENT, "r", encoding="utf-8") as f:
        content = f.read()

    assert "start=ep_" in content, "Episode deep link must include explicit ep_ prefix"
    assert "kinochi_mvp_bot" in content, "Episode component must fallback to kinochi_mvp_bot"

