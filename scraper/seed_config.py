"""
TMDb Top Seed Ingestor Configuration & Routing Module (S2).
Re-exports from app.core.seed_config for unified single-source-of-truth configuration.
"""
from app.core.seed_config import (
    SEED_MOVIE_TARGET,
    SEED_TV_TARGET,
    SEED_INCLUDE_SERIES,
    SEED_MIN_VOTE_COUNT,
    SEED_MIN_RATING,
    SEED_EXCLUDE_ADULT,
    SEED_BATCH_SIZE,
    SEED_NOT_FOUND_RETRY_DAYS,
    SEED_PRIORITY,
    SEED_SEARCH_DELAY_SECONDS,
    SEED_SEARCH_CONCURRENCY,
    is_tmdb_anime,
    get_target_sources_for_seed,
)

__all__ = [
    "SEED_MOVIE_TARGET",
    "SEED_TV_TARGET",
    "SEED_INCLUDE_SERIES",
    "SEED_MIN_VOTE_COUNT",
    "SEED_MIN_RATING",
    "SEED_EXCLUDE_ADULT",
    "SEED_BATCH_SIZE",
    "SEED_NOT_FOUND_RETRY_DAYS",
    "SEED_PRIORITY",
    "SEED_SEARCH_DELAY_SECONDS",
    "SEED_SEARCH_CONCURRENCY",
    "is_tmdb_anime",
    "get_target_sources_for_seed",
]
