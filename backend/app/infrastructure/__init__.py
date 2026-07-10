"""
Infrastructure Layer — database models, repositories, external integrations.

This is the outermost layer (along with api/).  It implements the
repository interfaces defined in the Domain layer using concrete
technologies: SQLAlchemy for DB, aiohttp/httpx for Telegram API,
redis-py for caching.

Sub-packages:
  - db/          SQLAlchemy models, concrete repository implementations, session factory
  - telegram/    Wrappers around Telegram Bot API (send file, check membership)
  - cache/       Redis client wrappers (key-value, rate limiter)
  - external/    Third-party API clients (IMDb/TMDB — future, v1.1+)
"""
