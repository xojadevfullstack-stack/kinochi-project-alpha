import pytest
import sys
import os

from pathlib import Path

scraper_dir = Path(__file__).resolve().parent.parent.parent / "scraper"
if str(scraper_dir) not in sys.path:
    sys.path.insert(0, str(scraper_dir))

from smart_enricher import score_tmdb_candidate


def test_reject_false_match_tokyo_ghoul_for_gul():
    """
    Qisqa nomli film (masalan 'Gul') tasodifiy yapon animesi (Tokyo Ghoul)
    bilan soxta mos kelmasligi (false match bo'lmasligi) kerak.
    """
    tokyo_ghoul_candidate = {
        "title": "Tokyo Ghoul",
        "original_title": "東京喰種 トーキョーグール",
        "release_year": 2017,
        "poster_url": "https://image.tmdb.org/t/p/w500/m6MzYJVfXMjN4E1JB2pc1iud3gI.jpg",
    }
    score = score_tmdb_candidate(
        candidate=tokyo_ghoul_candidate,
        query="Gul",
        target_year=2018,
    )
    # Soxta moslik qat'iyan rad etilishi kerak (-1.0)
    assert score < 0.0, f"False match qabul qilinib ketdi! Ball: {score}"


def test_accept_true_match_monstrum():
    """Haqiqiy moslik 'Monstrum' yuqori ball olishi kerak."""
    monstrum_candidate = {
        "title": "Monstrum",
        "original_title": "Mulgoe",
        "release_year": 2017,
        "poster_url": "https://image.tmdb.org/t/p/w500/monstrum.jpg",
    }
    score = score_tmdb_candidate(
        candidate=monstrum_candidate,
        query="Monstrum",
        target_year=2018,
    )
    assert score >= 60.0, f"Haqiqiy moslik qabul qilinmadi! Ball: {score}"


def test_accept_true_match_salmokji():
    """Haqiqiy koreys horror filmi 'Salmokji' mos kelishi kerak."""
    salmokji_candidate = {
        "title": "Salmokji",
        "original_title": "살목지",
        "release_year": 2026,
        "poster_url": "https://image.tmdb.org/t/p/w500/salmokji.jpg",
    }
    score = score_tmdb_candidate(
        candidate=salmokji_candidate,
        query="Salmokji",
        target_year=2026,
    )
    assert score >= 60.0, f"Haqiqiy moslik qabul qilinmadi! Ball: {score}"
