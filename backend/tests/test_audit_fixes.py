import pytest
from scraper.tmdb_top_ingestor import evaluate_candidate_match


def test_sf_001_adversarial_matcher_no_substring_false_positive():
    """
    SF-001: Substring trap bo'yicha turli xil filmlar (masalan 'Drive' va 'Drive Angry')
    yoki nomsiz yilda sikvellarning soxta ijobiy (False Positive) mos kelishini oldini olish.
    """
    # 1. Drive (2011) vs Drive Angry (2011) - turli filmlar, bir xil yil
    matched, reason = evaluate_candidate_match(
        seed_title_ru="Драйв",
        seed_title_en="Drive",
        seed_orig_title="Drive",
        seed_year=2011,
        scraped_title="Drive Angry / G'azabli drayv",
        scraped_year=2011,
        scraped_url="https://uzmovi.tv/803-drive-angry.html",
    )
    assert matched is False, f"Drive va Drive Angry mos kelmasligi kerak! Sabab: {reason}"

    # 2. Avatar: The Way of Water (2022) vs Avatar (scraped_year is None)
    matched2, reason2 = evaluate_candidate_match(
        seed_title_ru="Аватар: Путь воды",
        seed_title_en="Avatar: The Way of Water",
        seed_orig_title="Avatar: The Way of Water",
        seed_year=2022,
        scraped_title="Avatar",
        scraped_year=None,
        scraped_url="https://uzmovi.tv/103-avatar.html",
    )
    assert matched2 is False, f"Avatar 2 (subtitle) va Avatar (no year) mos kelmasligi kerak! Sabab: {reason2}"
