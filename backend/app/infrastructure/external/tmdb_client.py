"""
TMDb (The Movie Database) External API Client.
Fetches movie and TV series metadata, credits, posters, and YouTube trailers.
"""
import logging
from typing import Any
import httpx
from app.core.config import settings
from app.core.cache import get_cache, set_cache

logger = logging.getLogger(__name__)

TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/w500"


class TMDbClient:
    def __init__(self, api_key: str | None = None):
        self.api_key = (api_key or settings.TMDB_API_KEY).strip()

    def _get_headers_and_params(self) -> tuple[dict[str, str], dict[str, str]]:
        headers = {"Accept": "application/json"}
        params: dict[str, str] = {}
        if not self.api_key:
            return headers, params

        if self.api_key.startswith("ey") or len(self.api_key) > 50:
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            params["api_key"] = self.api_key
        return headers, params

    async def search(self, query: str, content_type: str = "movie") -> list[dict[str, Any]]:
        """
        Search for movies or TV shows on TMDb.
        content_type: 'movie' or 'tv'
        """
        if not self.api_key:
            logger.warning("TMDB_API_KEY is not configured.")
            return []

        clean_query = query.strip()
        if not clean_query:
            return []

        endpoint_type = "tv" if content_type in ("tv", "series") else "movie"
        cache_key = f"cache:tmdb:search:{endpoint_type}:{clean_query.lower()}"
        cached = await get_cache(cache_key)
        if cached:
            return cached

        headers, base_params = self._get_headers_and_params()
        params = {**base_params, "query": clean_query, "language": "ru-RU"}

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{TMDB_BASE_URL}/search/{endpoint_type}", headers=headers, params=params)
                if resp.status_code != 200:
                    logger.error(f"TMDb search failed ({resp.status_code}): {resp.text}")
                    return []
                data = resp.json()
            except Exception as e:
                logger.error(f"TMDb search request error: {e}")
                return []

        results = data.get("results", [])
        # If no results found in Russian, try international/English search
        if not results:
            params["language"] = "en-US"
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    resp = await client.get(f"{TMDB_BASE_URL}/search/{endpoint_type}", headers=headers, params=params)
                    if resp.status_code == 200:
                        results = resp.json().get("results", [])
                except Exception as e:
                    logger.error(f"TMDb search fallback request error: {e}")

        items = []
        for item in results:
            title = item.get("title") if endpoint_type == "movie" else item.get("name")
            orig_title = item.get("original_title") if endpoint_type == "movie" else item.get("original_name")
            release_date = item.get("release_date") if endpoint_type == "movie" else item.get("first_air_date")
            year = None
            if release_date and len(release_date) >= 4 and release_date[:4].isdigit():
                year = int(release_date[:4])

            poster_path = item.get("poster_path")
            poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None

            items.append({
                "id": item["id"],
                "tmdb_id": item["id"],
                "content_type": "series" if endpoint_type == "tv" else "movie",
                "title": title or orig_title or "Noma'lum",
                "original_title": orig_title,
                "release_year": year,
                "poster_url": poster_url,
                "overview": item.get("overview") or "",
                "vote_average": round(item.get("vote_average", 0.0), 1),
            })

        # Cache search result for 1 hour (3600 seconds)
        await set_cache(cache_key, items, ttl_seconds=3600)
        return items

    async def get_details(self, tmdb_id: int, content_type: str = "movie") -> dict[str, Any] | None:
        """
        Fetch full details for movie or TV show including credits and videos.
        """
        if not self.api_key:
            return None

        endpoint_type = "tv" if content_type in ("tv", "series") else "movie"
        cache_key = f"cache:tmdb:details:{endpoint_type}:{tmdb_id}"
        cached = await get_cache(cache_key)
        if cached:
            return cached

        headers, base_params = self._get_headers_and_params()
        params = {
            **base_params,
            "append_to_response": "videos,credits",
            "language": "ru-RU",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                resp = await client.get(f"{TMDB_BASE_URL}/{endpoint_type}/{tmdb_id}", headers=headers, params=params)
                if resp.status_code != 200:
                    logger.error(f"TMDb details failed ({resp.status_code}) for ID {tmdb_id}: {resp.text}")
                    return None
                data = resp.json()
            except Exception as e:
                logger.error(f"TMDb details request error: {e}")
                return None

        # Fallback overview if Russian is empty
        overview = data.get("overview") or ""
        if not overview:
            en_params = {**base_params, "language": "en-US"}
            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    resp_en = await client.get(f"{TMDB_BASE_URL}/{endpoint_type}/{tmdb_id}", headers=headers, params=en_params)
                    if resp_en.status_code == 200:
                        overview = resp_en.json().get("overview") or ""
                except Exception:
                    pass

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
            # Prefer official trailer if available
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

        poster_path = data.get("poster_path")
        poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None

        vote_avg = data.get("vote_average")
        tmdb_rating = round(vote_avg, 1) if vote_avg is not None else None

        result = {
            "tmdb_id": tmdb_id,
            "content_type": "series" if endpoint_type == "tv" else "movie",
            "title": title or orig_title or "Noma'lum",
            "original_title": orig_title,
            "overview": overview,
            "release_year": year,
            "runtime": runtime,
            "tmdb_rating": tmdb_rating,
            "poster_url": poster_url,
            "trailer_url": trailer_url,
            "director": director_str,
            "cast": cast_str,
            "genres_raw": genres_list,
            "genres_str": genres_names,
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

        # Cache details for 24 hours (86400 seconds)
        await set_cache(cache_key, result, ttl_seconds=86400)
        return result


tmdb_client = TMDbClient()
