"""
TMDb (The Movie Database) External API Client.
Fetches movie and TV series metadata, credits, posters, trailers, translations, and external IDs.
Includes conservative token-bucket rate limiter, 429 Retry-After handling, and response caching.
"""
import os
import time
import asyncio
import logging
from typing import Any
import httpx
from app.core.config import settings
from app.core.cache import get_cache, set_cache

logger = logging.getLogger(__name__)

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


class TMDbRateLimiter:
    """
    Asinxron token-bucket rate limiter.
    TMDb API ga so'rovlar chastotasini xavfsiz chegarada ushlab turadi.
    """
    def __init__(self, requests_per_second: float = 10.0, burst: int = 10):
        self.rate = max(1.0, requests_per_second)
        self.capacity = max(1, burst)
        self.tokens = float(self.capacity)
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.last_update = now
            self.tokens = min(float(self.capacity), self.tokens + elapsed * self.rate)
            if self.tokens < 1.0:
                wait_time = (1.0 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0.0
            else:
                self.tokens -= 1.0


class TMDbClient:
    def __init__(
        self,
        api_key: str | None = None,
        rate_limit: float | None = None,
        timeout: float | None = None,
    ):
        self._api_key = api_key
        r_limit = rate_limit or float(os.getenv("TMDB_RATE_LIMIT", "10.0"))
        self._rate_limiter = TMDbRateLimiter(requests_per_second=r_limit, burst=int(r_limit))
        self._timeout = timeout or float(os.getenv("TMDB_TIMEOUT", "10.0"))

    @property
    def api_key(self) -> str:
        if self._api_key is not None:
            return self._api_key.strip()
        return (settings.TMDB_API_KEY or "").strip()

    def _get_headers_and_params(self) -> tuple[dict[str, str], dict[str, str]]:
        headers = {"Accept": "application/json"}
        params: dict[str, str] = {}
        key = self.api_key
        if not key:
            return headers, params

        if key.startswith("ey") or len(key) > 50:
            headers["Authorization"] = f"Bearer {key}"
        else:
            params["api_key"] = key
        return headers, params

    async def _request_with_retry(
        self,
        endpoint: str,
        params: dict[str, Any],
        timeout: float | None = None,
        max_retries: int = 3,
    ) -> dict[str, Any] | None:
        """
        Rate-limited va 429 Retry-After himoyalangan xavfsiz HTTP so'rov.
        Hech qanday maxfiy API kalitlarini loglarga chiqarmaydi.
        """
        if not self.api_key:
            logger.warning("TMDB_API_KEY sozlanmagan.")
            return None

        req_timeout = timeout or self._timeout
        headers, base_params = self._get_headers_and_params()
        merged_params = {**base_params, **params}
        url = f"{TMDB_BASE_URL}/{endpoint.lstrip('/')}"

        for attempt in range(max_retries):
            await self._rate_limiter.acquire()
            try:
                async with httpx.AsyncClient(timeout=req_timeout) as client:
                    resp = await client.get(url, headers=headers, params=merged_params)
                    if resp.status_code == 200:
                        return resp.json()
                    elif resp.status_code == 429:
                        retry_after_str = resp.headers.get("Retry-After", "1.0")
                        try:
                            retry_after = float(retry_after_str)
                        except (ValueError, TypeError):
                            retry_after = 1.0
                        retry_after = min(max(retry_after, 0.5), 10.0)
                        logger.warning(
                            f"TMDb 429 Rate Limit (urinish {attempt + 1}/{max_retries}). "
                            f"{retry_after} soniya kutilmoqda..."
                        )
                        await asyncio.sleep(retry_after)
                        continue
                    elif resp.status_code == 404:
                        logger.info(f"TMDb 404: so'ralgan resurs topilmadi: {endpoint}")
                        return None
                    else:
                        logger.warning(f"TMDb so'rov xatoligi (HTTP {resp.status_code}): {resp.text[:100]}")
                        if resp.status_code in (500, 502, 503, 504) and attempt < max_retries - 1:
                            await asyncio.sleep(1.0 * (attempt + 1))
                            continue
                        return None
            except httpx.RequestError as e:
                logger.warning(f"TMDb tarmoq xatoligi (urinish {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1.0 * (attempt + 1))
                    continue
                return None
            except Exception as e:
                logger.error(f"Kutilmagan TMDb xatoligi: {e}")
                return None
        return None

    async def list_top_rated(self, kind: str = "movie", page: int = 1) -> dict[str, Any]:
        """
        TMDb Top-Rated filmlar yoki seriallar ro'yxatini sahifalab oladi.
        kind: 'movie' yoki 'tv' (shuningdek 'series' ham qabul qilinadi)
        page: 1..1000
        """
        endpoint_type = "tv" if kind in ("tv", "series") else "movie"
        cache_key = f"cache:tmdb:top_rated:{endpoint_type}:{page}"
        cached = await get_cache(cache_key)
        if cached:
            return cached

        data = await self._request_with_retry(
            f"{endpoint_type}/top_rated",
            params={"page": page, "language": "ru-RU"},
        )
        if not data:
            return {"page": page, "results": [], "total_pages": 0, "total_results": 0}

        await set_cache(cache_key, data, ttl_seconds=86400)
        return data

    async def list_popular(self, kind: str = "movie", page: int = 1) -> dict[str, Any]:
        """
        TMDb Popular filmlar yoki seriallar ro'yxatini sahifalab oladi.
        kind: 'movie' yoki 'tv' (shuningdek 'series' ham qabul qilinadi)
        page: 1..1000
        """
        endpoint_type = "tv" if kind in ("tv", "series") else "movie"
        cache_key = f"cache:tmdb:popular:{endpoint_type}:{page}"
        cached = await get_cache(cache_key)
        if cached:
            return cached

        data = await self._request_with_retry(
            f"{endpoint_type}/popular",
            params={"page": page, "language": "ru-RU"},
        )
        if not data:
            return {"page": page, "results": [], "total_pages": 0, "total_results": 0}

        await set_cache(cache_key, data, ttl_seconds=86400)
        return data

    # Aliases
    async def get_popular_movies(self, page: int = 1) -> dict[str, Any]:
        return await self.list_popular("movie", page=page)

    async def get_popular_tv(self, page: int = 1) -> dict[str, Any]:
        return await self.list_popular("tv", page=page)

    async def get_top_rated_movies(self, page: int = 1) -> dict[str, Any]:
        return await self.list_top_rated("movie", page=page)

    async def get_top_rated_tv(self, page: int = 1) -> dict[str, Any]:
        return await self.list_top_rated("tv", page=page)

    async def search(self, query: str, content_type: str = "movie") -> list[dict[str, Any]]:
        """
        Search for movies or TV shows on TMDb.
        content_type: 'movie' or 'tv'
        Supports both title keywords and direct TMDb numeric IDs.
        """
        if not self.api_key:
            logger.warning("TMDB_API_KEY sozlanmagan.")
            return []

        clean_query = query.strip()
        if not clean_query:
            return []

        endpoint_type = "tv" if content_type in ("tv", "series") else "movie"
        cache_key = f"cache:tmdb:search:{endpoint_type}:{clean_query.lower()}"
        cached = await get_cache(cache_key)
        if cached:
            return cached

        items: list[dict[str, Any]] = []
        seen_ids: set[int] = set()

        # Direct numeric ID check
        if clean_query.isdigit():
            try:
                direct_id = int(clean_query)
                direct_data = await self.get_details(direct_id, kind=endpoint_type)
                if direct_data:
                    items.append({
                        "id": direct_data["tmdb_id"],
                        "tmdb_id": direct_data["tmdb_id"],
                        "content_type": direct_data["content_type"],
                        "title": direct_data["title"],
                        "original_title": direct_data.get("original_title"),
                        "release_year": direct_data.get("release_year"),
                        "poster_url": direct_data.get("poster_url"),
                        "overview": direct_data.get("overview") or "",
                        "vote_average": direct_data.get("tmdb_rating") or 0.0,
                        "adult": bool(direct_data.get("adult", False)),
                    })
                    seen_ids.add(direct_id)
            except Exception as e:
                logger.warning(f"To'g'ridan-to'g'ri TMDb ID qidiruvi xatoligi ({clean_query}): {e}")

        # Search in Russian first
        data = await self._request_with_retry(
            f"search/{endpoint_type}",
            params={"query": clean_query, "language": "ru-RU", "include_adult": "true"},
        )
        results = (data or {}).get("results", [])

        # Fallback to international search if Russian returned empty
        if not results:
            data_en = await self._request_with_retry(
                f"search/{endpoint_type}",
                params={"query": clean_query, "language": "en-US", "include_adult": "true"},
            )
            results = (data_en or {}).get("results", [])

        for item in results:
            item_id = item["id"]
            if item_id in seen_ids:
                continue
            seen_ids.add(item_id)

            title = item.get("title") if endpoint_type == "movie" else item.get("name")
            orig_title = item.get("original_title") if endpoint_type == "movie" else item.get("original_name")
            release_date = item.get("release_date") if endpoint_type == "movie" else item.get("first_air_date")
            year = None
            if release_date and len(release_date) >= 4 and release_date[:4].isdigit():
                year = int(release_date[:4])

            poster_path = item.get("poster_path")
            poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None

            items.append({
                "id": item_id,
                "tmdb_id": item_id,
                "content_type": "series" if endpoint_type == "tv" else "movie",
                "title": title or orig_title or "Noma'lum",
                "original_title": orig_title,
                "release_year": year,
                "poster_url": poster_url,
                "overview": item.get("overview") or "",
                "vote_average": round(item.get("vote_average", 0.0), 1),
                "adult": bool(item.get("adult", False)),
            })

        if items:
            await set_cache(cache_key, items, ttl_seconds=3600)
        return items

    async def get_details(
        self,
        tmdb_id: int,
        kind: str = "movie",
        content_type: str | None = None,
    ) -> dict[str, Any] | None:
        """
        Fetch full details for movie or TV show including credits, videos, translations, and external IDs.
        kind / content_type: 'movie' or 'tv'
        """
        if not self.api_key:
            return None

        effective_kind = content_type or kind or "movie"
        endpoint_type = "tv" if effective_kind in ("tv", "series") else "movie"
        cache_key = f"cache:tmdb:details:{endpoint_type}:{tmdb_id}"
        cached = await get_cache(cache_key)
        if cached:
            return cached

        data = await self._request_with_retry(
            f"{endpoint_type}/{tmdb_id}",
            params={
                "append_to_response": "videos,credits,translations,external_ids",
                "language": "ru-RU",
            },
        )
        if not data:
            return None

        # Fallback overview if Russian is empty
        overview = data.get("overview") or ""
        if not overview:
            en_data = await self._request_with_retry(
                f"{endpoint_type}/{tmdb_id}",
                params={"language": "en-US"},
            )
            if en_data:
                overview = en_data.get("overview") or ""

        title = data.get("title") if endpoint_type == "movie" else data.get("name")
        orig_title = data.get("original_title") if endpoint_type == "movie" else data.get("original_name")
        release_date = data.get("release_date") if endpoint_type == "movie" else data.get("first_air_date")
        year = None
        if release_date and len(release_date) >= 4 and release_date[:4].isdigit():
            year = int(release_date[:4])

        runtime = data.get("runtime")
        if not runtime and endpoint_type == "tv":
            ep_runtimes = data.get("episode_run_time") or []
            if ep_runtimes:
                runtime = ep_runtimes[0]

        # Trailer selection from YouTube
        trailer_url = None
        videos = data.get("videos", {}).get("results", [])
        youtube_trailers = [
            v for v in videos
            if v.get("site") == "YouTube" and v.get("type") in ("Trailer", "Teaser") and v.get("key")
        ]
        if youtube_trailers:
            official = next((v for v in youtube_trailers if v.get("official") and v.get("type") == "Trailer"), None)
            best_video = official or youtube_trailers[0]
            trailer_url = f"https://www.youtube.com/watch?v={best_video['key']}"

        # Director / Creators
        credits_data = data.get("credits", {})
        crew = credits_data.get("crew", [])
        directors = [c.get("name") for c in crew if c.get("job") == "Director" and c.get("name")]
        if not directors and endpoint_type == "tv":
            directors = [c.get("name") for c in data.get("created_by", []) if c.get("name")]
        director_str = ", ".join(directors[:2]) if directors else None

        # Top 5 Cast
        cast_list = [c.get("name") for c in credits_data.get("cast", [])[:5] if c.get("name")]
        cast_str = ", ".join(cast_list) if cast_list else None

        # Genres
        genres_raw = data.get("genres", [])
        genres_list = [{"id": g.get("id"), "name": g.get("name")} for g in genres_raw]
        genres_names = ", ".join([g.get("name") for g in genres_raw if g.get("name")])

        # Poster lookup (original / clean en poster to avoid Russian text overlays)
        poster_path = data.get("poster_path")
        try:
            en_data = await self._request_with_retry(
                f"{endpoint_type}/{tmdb_id}",
                params={"language": "en-US"},
                timeout=6.0,
            )
            if en_data and en_data.get("poster_path"):
                poster_path = en_data["poster_path"]
        except Exception as e:
            logger.debug(f"TMDb toza posterni olishda xatolik: {e}")

        poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None

        vote_avg = data.get("vote_average")
        tmdb_rating = round(vote_avg, 1) if vote_avg is not None else None
        vote_count = data.get("vote_count") or 0
        popularity = data.get("popularity") or 0.0

        # Translations extraction
        trans_list = data.get("translations", {}).get("translations", [])
        title_ru = title
        title_en = orig_title
        title_uz = None
        for tr in trans_list:
            iso = tr.get("iso_639_1")
            t_data = tr.get("data") or {}
            cand_title = t_data.get("title") or t_data.get("name")
            if not cand_title:
                continue
            if iso == "ru" and not title_ru:
                title_ru = cand_title
            elif iso == "en" and not title_en:
                title_en = cand_title
            elif iso == "uz":
                title_uz = cand_title

        # External IDs extraction
        ext_ids = data.get("external_ids") or {}
        imdb_id = ext_ids.get("imdb_id")
        tvdb_id = ext_ids.get("tvdb_id")

        result = {
            "tmdb_id": tmdb_id,
            "content_type": "series" if endpoint_type == "tv" else "movie",
            "title": title or orig_title or "Noma'lum",
            "original_title": orig_title,
            "title_ru": title_ru or title or orig_title,
            "title_en": title_en or orig_title or title,
            "title_uz": title_uz,
            "overview": overview,
            "release_year": year,
            "runtime": runtime,
            "tmdb_rating": tmdb_rating,
            "vote_average": tmdb_rating,
            "vote_count": vote_count,
            "popularity": popularity,
            "poster_url": poster_url,
            "trailer_url": trailer_url,
            "director": director_str,
            "cast": cast_str,
            "genres_raw": genres_list,
            "genres_str": genres_names,
            "adult": bool(data.get("adult", False)),
            "imdb_id": imdb_id,
            "tvdb_id": tvdb_id,
            "external_ids": ext_ids,
            "original_language": data.get("original_language"),
        }

        # TV-specific metadata
        if endpoint_type == "tv":
            seasons_info = []
            for s in data.get("seasons", []):
                s_num = s.get("season_number")
                if s_num is not None and s_num > 0:
                    seasons_info.append({
                        "season_number": s_num,
                        "name": s.get("name") or f"{s_num}-mavsum",
                        "episode_count": s.get("episode_count") or 0,
                    })
            result["seasons"] = seasons_info
            result["number_of_seasons"] = data.get("number_of_seasons")
            result["number_of_episodes"] = data.get("number_of_episodes")

        # Cache details for 24 hours
        await set_cache(cache_key, result, ttl_seconds=86400)
        return result


tmdb_client = TMDbClient()
