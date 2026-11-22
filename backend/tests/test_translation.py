import pytest
from unittest.mock import patch, MagicMock
from app.infrastructure.external.genre_mapper import map_tmdb_genres
from app.infrastructure.external.translator import TranslatorService


def test_map_tmdb_genres():
    raw = [
        {"id": 28, "name": "Боевик"},
        {"id": 12, "name": "Приключения"},
        {"id": 878, "name": "Научная фантастика"},
    ]
    genres = map_tmdb_genres(raw)
    assert "Jangari" in genres
    assert "Sarguzasht" in genres
    assert "Ilmiy fantastika" in genres


@pytest.mark.asyncio
async def test_translator_service_mock():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Kuper oilasi bilan yashaydi."}]
                }
            }
        ]
    }

    service = TranslatorService(api_key="mock_gemini_key")
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        with patch("app.infrastructure.external.translator.get_cache", return_value=None):
            with patch("app.infrastructure.external.translator.set_cache", return_value=True):
                text, ok = await service.translate_to_uzbek("Cooper lives with his family.")
                assert ok is True
                assert text == "Kuper oilasi bilan yashaydi."


@pytest.mark.asyncio
async def test_translator_title_mock():
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Iblislar qotili"}]
                }
            }
        ]
    }

    service = TranslatorService(api_key="mock_gemini_key")
    with patch("httpx.AsyncClient.post", return_value=mock_resp):
        with patch("app.infrastructure.external.translator.get_cache", return_value=None):
            with patch("app.infrastructure.external.translator.set_cache", return_value=True):
                title, ok = await service.translate_title_to_uzbek("Истребитель демонов", "Demon Slayer: Kimetsu no Yaiba")
                assert ok is True
                assert title == "Iblislar qotili"


@pytest.mark.asyncio
async def test_translate_to_uzbek_does_not_transliterate_russian_when_all_apis_fail():
    """Regression: never return 'V budushem...' gibberish marked as translated when APIs fail."""
    service = TranslatorService(api_key="")
    ru_text = "В будущем межзвёздные полёты стали обыденностью."
    with patch("app.infrastructure.external.translator.get_cache", return_value=None):
        with patch("app.infrastructure.external.translator.set_cache", return_value=True):
            with patch("httpx.AsyncClient.post", side_effect=Exception("network down")):
                with patch("httpx.AsyncClient.get", side_effect=Exception("network down")):
                    text, ok = await service.translate_to_uzbek(ru_text)
                    assert ok is False
                    assert text == ru_text


@pytest.mark.asyncio
async def test_translate_title_prefers_latin_en_title_over_cjk_original_on_fallback():
    """Regression: when APIs fail for Chinese/CJK movie, never output CJK title if English title exists."""
    service = TranslatorService(api_key="")
    with patch("app.infrastructure.external.translator.get_cache", return_value=None):
        with patch("app.infrastructure.external.translator.set_cache", return_value=True):
            with patch("httpx.AsyncClient.post", side_effect=Exception("network down")):
                with patch("httpx.AsyncClient.get", side_effect=Exception("network down")):
                    title, ok = await service.translate_title_to_uzbek(
                        "Через тернии к звёздам",
                        "星河入梦",
                        en_title="Per Aspera Ad Astra",
                    )
                    assert ok is False
                    assert title == "Per Aspera Ad Astra"


@pytest.mark.asyncio
async def test_tmdb_get_details_captures_en_title_even_when_original_title_is_cjk():
    """Regression: title_en must come from en-US data/translations, not be shadowed by CJK orig_title."""
    from app.infrastructure.external.tmdb_client import TMDbClient

    client = TMDbClient(api_key="dummy_key")
    ru_payload = {
        "id": 1359005,
        "title": "Через тернии к звёздам",
        "original_title": "星河入梦",
        "overview": "В будущем...",
        "release_date": "2026-01-01",
        "runtime": 111,
        "vote_average": 8.1,
        "genres": [],
        "videos": {"results": []},
        "credits": {"crew": [], "cast": []},
        "translations": {
            "translations": [
                {"iso_639_1": "en", "data": {"title": "Per Aspera Ad Astra"}},
            ]
        },
        "external_ids": {},
    }
    en_payload = {
        "id": 1359005,
        "title": "Per Aspera Ad Astra",
        "overview": "In the future...",
        "poster_path": "/abc.jpg",
        "credits": {"crew": [], "cast": []},
    }

    async def fake_request(endpoint, params=None, **kwargs):
        if params and params.get("language") == "en-US":
            return en_payload
        return ru_payload

    with patch("app.infrastructure.external.tmdb_client.get_cache", return_value=None):
        with patch("app.infrastructure.external.tmdb_client.set_cache", return_value=True):
            with patch.object(client, "_request_with_retry", side_effect=fake_request):
                details = await client.get_details(1359005, content_type="movie")
                assert details is not None
                assert details["original_title"] == "星河入梦"
                assert details["title_en"] == "Per Aspera Ad Astra"
