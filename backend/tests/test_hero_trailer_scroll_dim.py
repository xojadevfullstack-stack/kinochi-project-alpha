import os

def test_hero_trailer_scroll_dim_logic():
    path = os.path.join("website", "components", "media", "HeroTrailerBackdrop.tsx")
    assert os.path.exists(path), f"{path} must exist"
    
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Scroll event listener must be attached
    assert '"scroll"' in content or "'scroll'" in content, "Must listen to scroll event to restore details"
    # Dimmed state rather than full disappearance
    assert "isDimmed" in content or "dimmed" in content, "Must have dimmed state"
    # Should use semi-transparency for second-tier details
    assert "opacity-20" in content or "opacity-25" in content or "opacity-30" in content, \
        "Details must be semi-transparent when dimmed, not completely removed"
    # Floating sound and trailer view buttons must be removed
    assert "volume_off" not in content and "volume_up" not in content, \
        "Sound toggle button must be removed as requested"
    assert "Treylerni ko'rish" not in content and "Treylerni ko&apos;rish" not in content, \
        "Trailer view button must be removed from hero backdrop as requested"
