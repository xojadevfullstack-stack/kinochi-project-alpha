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
