import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def test_score_tmdb_candidate_rejects_noisy_concert_title_mismatch():
    """'Dream Galaxy' must not score >= 50 against 'BanG Dream! 11th☆LIVE DAY1...GALAXY to GALAXY'."""
    from scraper.smart_enricher import score_tmdb_candidate

    wrong_concert = {
        "id": 1298888,
        "title": "BanG Dream! 11th☆LIVE DAY1 : Poppin'Party×RAISE A SUILEN「GALAXY to GALAXY」",
        "original_title": "BanG Dream! 11th☆LIVE DAY1 : Poppin'Party×RAISE A SUILEN「GALAXY to GALAXY」",
        "release_year": 2023,
        "poster_url": "https://image.tmdb.org/t/p/w500/6fkS8ClkEO7tjoZtvDrDgKCS72c.jpg",
        "vote_average": 0.0,
        "genre_ids": [10402],
        "content_type": "movie",
    }
    score = score_tmdb_candidate(
        wrong_concert,
        query="Dream Galaxy",
        target_year=2026,
        expected_original_title="Dream Galaxy",
    )
    assert score < 50.0, f"Expected < 50.0 for noisy concert mismatch, got {score}"


def test_score_tmdb_candidate_prefers_exact_movie_match():
    from scraper.smart_enricher import score_tmdb_candidate

    exact_movie = {
        "id": 1359005,
        "title": "Per Aspera Ad Astra",
        "original_title": "星河入梦",
        "release_year": 2026,
        "poster_url": "https://image.tmdb.org/t/p/w500/cuNGOSr0oSuBm0uAa28516Iw3Bw.jpg",
        "vote_average": 8.1,
        "content_type": "movie",
    }
    score = score_tmdb_candidate(
        exact_movie,
        query="Per Aspera Ad Astra",
        target_year=2026,
        expected_original_title="Per Aspera Ad Astra",
    )
    assert score >= 90.0


def test_gemini_identify_movie_retries_503_and_requests_search_titles(monkeypatch):
    import asyncio
    from unittest.mock import AsyncMock
    import httpx
    import scraper.smart_enricher as se

    monkeypatch.setattr(se.settings, "GEMINI_API_KEY", "test-key")
    monkeypatch.setattr(se.asyncio, "sleep", AsyncMock())

    calls = []

    class FakeResp:
        def __init__(self, status_code, body):
            self.status_code = status_code
            self._body = body

        def json(self):
            return self._body

    class FakeClient:
        def __init__(self, *args, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def post(self, url, json=None, **kwargs):
            calls.append((url, json))
            if len(calls) == 1:
                return FakeResp(503, {"error": {"code": 503}})
            return FakeResp(
                200,
                {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "text": (
                                            '{"clean_uz_title": "Ouk Strit ko\'chasining oxiri",'
                                            ' "original_title": null,'
                                            ' "search_title_en": "The End of Oak Street",'
                                            ' "search_title_ru": "Конец Оук-Стрит",'
                                            ' "release_year": 2026}'
                                        )
                                    }
                                ]
                            }
                        }
                    ]
                },
            )

    monkeypatch.setattr(httpx, "AsyncClient", FakeClient)

    result = asyncio.run(se.gemini_identify_movie("Ouk Strit ko'chasining oxiri", year_hint=2026))
    assert result is not None
    assert result["search_title_en"] == "The End of Oak Street"
    # Must retry 503 on the SAME primary model instead of breaking immediately
    assert len(calls) == 2
    assert calls[0][0] == calls[1][0]
    # Must enforce JSON mime type and instruct search_title_en translation even when original_title is null
    payload = calls[0][1]
    assert payload["generationConfig"].get("responseMimeType") == "application/json"
    prompt_text = payload["contents"][0]["parts"][0]["text"]
    assert "search_title_en" in prompt_text and "tarjima" in prompt_text.lower()


def test_score_tmdb_candidate_matches_end_of_oak_street_via_search_title_en():
    from scraper.smart_enricher import score_tmdb_candidate

    cand = {
        "id": 1101383,
        "title": "The End of Oak Street",
        "original_title": "The End of Oak Street",
        "release_year": 2026,
        "poster_url": "https://image.tmdb.org/t/p/w500/abc.jpg",
        "vote_average": 0.0,
        "content_type": "movie",
    }
    score = score_tmdb_candidate(
        cand,
        query="The End of Oak Street",
        target_year=2026,
        expected_en_title="The End of Oak Street",
    )
    assert score >= 90.0


def test_pick_canonical_uzbek_title_preserves_uzbek_when_translation_fails():
    from scraper.smart_enricher import pick_canonical_uzbek_title

    # When translation returns False (fallback to English), keep existing Uzbek title
    assert (
        pick_canonical_uzbek_title(
            existing_title="Ouk Strit ko'chasining oxiri",
            translated_title="The End of Oak Street",
            is_translated=False,
            tmdb_title="The End of Oak Street",
            tmdb_original="The End of Oak Street",
        )
        == "Ouk Strit ko'chasining oxiri"
    )
    # When translation explicitly succeeds in Uzbek, accept canonical title
    assert (
        pick_canonical_uzbek_title(
            existing_title="Odam o'rgimchak",
            translated_title="O'rgimchak odam",
            is_translated=True,
            tmdb_title="Spider-Man",
            tmdb_original="Spider-Man",
        )
        == "O'rgimchak odam"
    )
