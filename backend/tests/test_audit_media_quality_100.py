import pytest
from unittest.mock import AsyncMock, patch
from app.infrastructure.external.tmdb_client import TMDbClient
from app.api.v1.audit import evaluate_series_issues
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel
from app.infrastructure.db.models.category import CategoryModel


@pytest.mark.asyncio
async def test_tmdb_client_includes_multilingual_videos_param():
    """TMDb get_details so'rovida include_video_language parametri uzatilishini tasdiqlaydi."""
    client = TMDbClient(api_key="test_key_xyz")
    mock_response = {
        "id": 207468,
        "name": "Kaiju No. 8",
        "original_name": "怪獣8号",
        "overview": "Kaiju No. 8 description in russian or fallback",
        "first_air_date": "2024-04-13",
        "poster_path": "/poster.jpg",
        "videos": {
            "results": [
                {
                    "site": "YouTube",
                    "type": "Trailer",
                    "key": "FsAKMsUjaK0",
                    "official": True,
                    "name": "Official Main Trailer"
                }
            ]
        }
    }

    with patch.object(client, "_request_with_retry", new=AsyncMock(return_value=mock_response)) as mock_req:
        details = await client.get_details(tmdb_id=207468, content_type="tv")
        
        # Verify call arguments to ensure include_video_language was requested
        assert mock_req.called
        call_params = mock_req.call_args_list[0][1]["params"]
        assert "include_video_language" in call_params
        assert "en" in call_params["include_video_language"]
        assert "ja" in call_params["include_video_language"]
        assert details is not None
        assert details["trailer_url"] == "https://www.youtube.com/watch?v=FsAKMsUjaK0"
        assert details["release_year"] == 2024


@pytest.mark.asyncio
async def test_series_with_trailer_is_100_percent_healthy():
    """Treyler va barcha maydonlari to'liq bo'lgan serialda hech qanday kamchilik (issues) bo'lmasligini tasdiqlaydi."""
    series = SeriesModel(
        id=1026,
        title="Kaiju: 8-son",
        poster_url="https://image.tmdb.org/t/p/w500/poster.jpg",
        trailer_url="https://www.youtube.com/watch?v=FsAKMsUjaK0",
        description="Bu kamida o'ttiz belgidan iborat to'liq va mukammal tavsif matnidir.",
        tmdb_id=207468,
        release_year=2024,
        source_id=1,
    )
    series.categories = [CategoryModel(id=2, name="Anime", slug="anime")]

    season = SeasonModel(id=1, series_id=1026, season_number=1, episode_count=1)
    episode = EpisodeModel(id=1, season_id=1, episode_number=1, title="1-qism", code="EP01")
    trans = EpisodeTranslationModel(
        id=1, episode_id=1, language="O'zbekcha", storage_channel_message_id=2700
    )
    episode.translations = [trans]
    season.episodes = [episode]
    series.seasons = [season]

    flags, issues = evaluate_series_issues(series)
    assert flags["has_trailer"] is True
    assert flags["has_video"] is True
    assert flags["has_poster"] is True
    assert flags["has_description"] is True
    assert flags["has_categories"] is True
    assert flags["has_tmdb"] is True
    assert len(issues) == 0, f"Kamchiliklar bo'lmasligi kerak: {[i.label for i in issues]}"
