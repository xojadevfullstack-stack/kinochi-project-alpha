from app.core.config import Settings
from app.core.seed_config import is_tmdb_anime, get_target_sources_for_seed


def test_seed_config_defaults():
    s = Settings(BOT_TOKEN="mock_bot_token", STORAGE_CHANNEL_ID="123")
    assert s.SEED_MOVIE_TARGET == 1000
    assert s.SEED_TV_TARGET == 500
    assert s.SEED_INCLUDE_SERIES is False
    assert s.SEED_MIN_VOTE_COUNT == 1000
    assert s.SEED_MIN_RATING == 7.0
    assert s.SEED_EXCLUDE_ADULT is True
    assert s.SEED_BATCH_SIZE == 20
    assert s.SEED_NOT_FOUND_RETRY_DAYS == 30
    assert s.SEED_PRIORITY == 100
    assert s.SEED_SEARCH_DELAY_SECONDS == 1.0
    assert s.SEED_SEARCH_CONCURRENCY == 2


def test_seed_config_env_override(monkeypatch):
    monkeypatch.setenv("SEED_MOVIE_TARGET", "500")
    monkeypatch.setenv("SEED_INCLUDE_SERIES", "true")
    monkeypatch.setenv("SEED_MIN_RATING", "8.0")
    s = Settings(BOT_TOKEN="mock_bot_token", STORAGE_CHANNEL_ID="123")
    assert s.SEED_MOVIE_TARGET == 500
    assert s.SEED_INCLUDE_SERIES is True
    assert s.SEED_MIN_RATING == 8.0


def test_anime_routing_rules():
    # 1. Japanese animation (Spirited Away, Naruto, etc.) -> Anime
    assert is_tmdb_anime([{"id": 16, "name": "Animation"}], "ja") is True
    assert is_tmdb_anime([16], "ja") is True
    assert is_tmdb_anime([{"id": 16, "name": "Мультфильм"}], "JA") is True

    # 2. American animation (Toy Story, Shrek, etc.) -> NOT anime (routed to Uzmovi/Asilmedia)
    assert is_tmdb_anime([{"id": 16, "name": "Animation"}], "en") is False

    # 3. Japanese Live-Action (Godzilla Minus One, Seven Samurai) -> NOT anime
    assert is_tmdb_anime([{"id": 28, "name": "Action"}], "ja") is False

    # 4. Standard Movie (Inception) -> NOT anime
    assert is_tmdb_anime([{"id": 878, "name": "Sci-Fi"}], "en") is False

    # 5. Missing / None values
    assert is_tmdb_anime(None, "ja") is False
    assert is_tmdb_anime([16], None) is False


def test_get_target_sources_for_seed():
    assert get_target_sources_for_seed(is_anime=True) == ["anitoob", "animeelar"]
    assert get_target_sources_for_seed(is_anime=False) == ["uzmovi", "asilmedia"]
