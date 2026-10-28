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

from app.infrastructure.external.translator import cyrillic_to_latin

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

        # Fetch English data for clean Latin poster, director and cast
        en_data = None
        poster_path = data.get("poster_path")
        try:
            en_data = await self._request_with_retry(
                f"{endpoint_type}/{tmdb_id}",
                params={"language": "en-US", "append_to_response": "credits"},
                timeout=6.0,
            )
            if en_data and en_data.get("poster_path"):
                poster_path = en_data["poster_path"]
        except Exception as e:
            logger.debug(f"TMDb toza posterni olishda xatolik: {e}")

        poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None

        # Director / Creators (prefer English/Latin names so no Russian Cyrillic leaks)
        en_credits = (en_data or {}).get("credits", {}) if en_data else {}
        en_crew = en_credits.get("crew", [])
        directors = [c.get("name") for c in en_crew if c.get("job") == "Director" and c.get("name")]
        if not directors and endpoint_type == "tv" and en_data:
            directors = [c.get("name") for c in en_data.get("created_by", []) if c.get("name")]

        # Fallback to Russian response if English crew missing, but transliterate to Latin
        if not directors:
            ru_crew = data.get("credits", {}).get("crew", [])
            directors = [cyrillic_to_latin(c.get("name")) for c in ru_crew if c.get("job") == "Director" and c.get("name")]
            if not directors and endpoint_type == "tv":
                directors = [cyrillic_to_latin(c.get("name")) for c in data.get("created_by", []) if c.get("name")]

        director_str = ", ".join(directors[:2]) if directors else None

        # Top 5 Cast (prefer English/Latin names)
        cast_list = [c.get("name") for c in en_credits.get("cast", [])[:5] if c.get("name")]
        if not cast_list:
            ru_cast = data.get("credits", {}).get("cast", [])[:5]
            cast_list = [cyrillic_to_latin(c.get("name")) for c in ru_cast if c.get("name")]
        cast_str = ", ".join(cast_list) if cast_list else None

        # Genres
        genres_raw = data.get("genres", [])
        genres_list = [{"id": g.get("id"), "name": g.get("name")} for g in genres_raw]
        genres_names = ", ".join([g.get("name") for g in genres_raw if g.get("name")])

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


    async def get_credits_and_details(
        self,
        tmdb_id: int,
        kind: str = "movie",
    ) -> dict[str, Any]:
        """
        TMDb orqali Suratga olish guruhi (Aktyorlar, Rejissyor, Muallif, Produserlar)
        hamda film/serialning qo'shimcha parametrlarini (Asl nomi, Davlati, Studiya, Holati)
        bitta birlashtirilgan paketda keshlab qaytaradi.
        """
        if not self.api_key or not tmdb_id:
            return {"items": [], "details": None}

        endpoint_type = "tv" if kind in ("tv", "series") else "movie"
        cache_key = f"tmdb:credits_and_details:{endpoint_type}:{tmdb_id}"
        cached = await get_cache(cache_key)
        if cached is not None:
            return cached

        # Parallel fetch details and credits with ru-RU (fallback en-US)
        details_task = self._request_with_retry(
            f"{endpoint_type}/{tmdb_id}",
            params={"language": "ru-RU"},
        )
        credits_task = self._request_with_retry(
            f"{endpoint_type}/{tmdb_id}/credits",
            params={"language": "ru-RU"},
        )
        details_raw, credits_raw = await asyncio.gather(details_task, credits_task)

        if not details_raw:
            details_raw = await self._request_with_retry(
                f"{endpoint_type}/{tmdb_id}",
                params={"language": "en-US"},
            )
        if not credits_raw:
            credits_raw = await self._request_with_retry(
                f"{endpoint_type}/{tmdb_id}/credits",
                params={"language": "en-US"},
            )

        details_raw = details_raw or {}
        credits_raw = credits_raw or {}

        items: list[dict[str, Any]] = []
        seen_ids: set[int] = set()

        # 1. Creators (for TV)
        for creator in details_raw.get("created_by", []):
            cid = creator.get("id")
            if not cid or cid in seen_ids:
                continue
            seen_ids.add(cid)
            name = creator.get("name") or creator.get("original_name") or "Muallif"
            profile_path = creator.get("profile_path")
            photo_url = f"{TMDB_IMAGE_BASE}{profile_path}" if profile_path else None
            items.append({
                "id": cid,
                "name": name,
                "role": "Rejissyor / Muallif",
                "character": "Creator",
                "photo_url": photo_url,
                "order": 0,
            })

        # 2. Key Crew mapping
        job_map = {
            "Director": "Rejissyor",
            "Screenplay": "Ssenariy muallifi",
            "Writer": "Ssenariy muallifi",
            "Story": "Ssenariy muallifi",
            "Producer": "Produser",
            "Executive Producer": "Bosh produser",
            "Director of Photography": "Operator",
            "Original Music Composer": "Bastakor",
            "Music": "Bastakor",
        }
        crew_raw = credits_raw.get("crew", [])
        key_crew_items: list[dict[str, Any]] = []
        for member in crew_raw:
            job = member.get("job")
            if job not in job_map:
                continue
            pid = member.get("id")
            if not pid or pid in seen_ids:
                continue
            seen_ids.add(pid)
            name = member.get("name") or member.get("original_name") or "Ijodkor"
            profile_path = member.get("profile_path")
            photo_url = f"{TMDB_IMAGE_BASE}{profile_path}" if profile_path else None

            key_crew_items.append({
                "id": pid,
                "name": name,
                "role": job_map[job],
                "character": job,
                "photo_url": photo_url,
                "order": 1,
            })
            if len(key_crew_items) >= 8:
                break

        # 3. Actors (Cast)
        cast_raw = credits_raw.get("cast", [])
        cast_items: list[dict[str, Any]] = []
        for member in cast_raw[:16]:
            pid = member.get("id")
            if not pid or pid in seen_ids:
                continue
            seen_ids.add(pid)
            name = member.get("name") or member.get("original_name") or "Aktyor"
            profile_path = member.get("profile_path")
            photo_url = f"{TMDB_IMAGE_BASE}{profile_path}" if profile_path else None
            character = member.get("character")

            cast_items.append({
                "id": pid,
                "name": name,
                "role": "Aktyor",
                "character": character,
                "photo_url": photo_url,
                "order": 2,
            })

        # Combine: Creators & Key Directors first, then top actors, then remaining key crew
        items = items + key_crew_items[:3] + cast_items + key_crew_items[3:]

        # 4. Details dictionary
        country_map = {
            "United States of America": "AQSH",
            "United States": "AQSH",
            "United Kingdom": "Buyuk Britaniya",
            "Russia": "Rossiya",
            "France": "Fransiya",
            "Germany": "Germaniya",
            "Japan": "Yaponiya",
            "South Korea": "Janubiy Koreya",
            "Turkey": "Turkiya",
            "India": "Hindiston",
            "Uzbekistan": "O'zbekiston",
            "Canada": "Kanada",
            "Spain": "Ispaniya",
            "Italy": "Italiya",
            "China": "Xitoy",
        }
        status_map = {
            "Ended": "Tugallangan",
            "Returning Series": "Davom etmoqda",
            "Released": "Premyera qilingan",
            "In Production": "Suratga olinmoqda",
            "Post Production": "Tayyorlanmoqda",
        }

        raw_countries = [c.get("name") for c in details_raw.get("production_countries", []) if c.get("name")]
        countries = [country_map.get(c, c) for c in raw_countries[:4]]

        companies = [c.get("name") for c in details_raw.get("production_companies", [])[:4] if c.get("name")]

        raw_status = details_raw.get("status")
        status = status_map.get(raw_status, raw_status) if raw_status else None

        orig_title = details_raw.get("original_title") or details_raw.get("original_name")
        release_date = details_raw.get("release_date") or details_raw.get("first_air_date")

        runtime = None
        if endpoint_type == "movie" and details_raw.get("runtime"):
            runtime = f"{details_raw.get('runtime')} daqiqa"
        elif endpoint_type == "tv" and details_raw.get("number_of_episodes"):
            ep_time = details_raw.get("episode_run_time")
            if ep_time and len(ep_time) > 0:
                runtime = f"{details_raw.get('number_of_episodes')} qism (~{ep_time[0]} daqiqa)"
            else:
                runtime = f"{details_raw.get('number_of_episodes')} qism"

        budget = None
        if details_raw.get("budget", 0) > 0:
            budget = f"${details_raw['budget']:,}"

        revenue = None
        if details_raw.get("revenue", 0) > 0:
            revenue = f"${details_raw['revenue']:,}"

        details_dict = {
            "original_title": orig_title,
            "countries": countries,
            "companies": companies,
            "release_date": release_date,
            "status": status,
            "runtime": runtime,
            "budget": budget,
            "revenue": revenue,
            "tagline": details_raw.get("tagline"),
        }

        result = {"items": items, "details": details_dict}
        await set_cache(cache_key, result, ttl_seconds=86400)
        return result

    async def get_credits(
        self,
        tmdb_id: int,
        kind: str = "movie",
    ) -> list[dict[str, Any]]:
        res = await self.get_credits_and_details(tmdb_id, kind=kind)
        return res.get("items", [])

    async def get_person_filmography(
        self,
        person_id: int,
    ) -> list[dict[str, Any]]:
        """
        Aktyor yoki ijodkorning TMDb dagi filmlari ro'yxatini (filmografiyasini) keshlab qaytaradi.
        """
        if not self.api_key or not person_id:
            return []

        cache_key = f"tmdb:person_filmography:{person_id}"
        cached = await get_cache(cache_key)
        if cached is not None:
            return cached

        data = await self._request_with_retry(
            f"person/{person_id}/movie_credits",
            params={"language": "ru-RU"},
        )
        if not data:
            data = await self._request_with_retry(
                f"person/{person_id}/movie_credits",
                params={"language": "en-US"},
            )

        if not data:
            await set_cache(cache_key, [], ttl_seconds=86400)
            return []

        cast_list = data.get("cast", [])
        crew_list = data.get("crew", [])

        key_jobs = {"Director", "Producer", "Screenplay", "Writer", "Director of Photography", "Original Music Composer"}
        priority_crew = [c for c in crew_list if c.get("job") in key_jobs]

        combined = []
        seen = set()
        for m in cast_list:
            mid = m.get("id")
            if mid and mid not in seen:
                seen.add(mid)
                combined.append(m)
        for m in priority_crew:
            mid = m.get("id")
            if mid and mid not in seen:
                seen.add(mid)
                combined.append(m)

        if not combined:
            combined = cast_list or crew_list

        combined.sort(key=lambda x: (x.get("vote_count") or 0) + (x.get("popularity") or 0), reverse=True)

        items: list[dict[str, Any]] = []
        seen_ids: set[int] = set()
        for m in combined[:25]:
            mid = m.get("id")
            if not mid or mid in seen_ids:
                continue
            seen_ids.add(mid)
            title = m.get("title") or m.get("original_title") or "Nomsiz film"
            rel_date = m.get("release_date") or ""
            year = int(rel_date[:4]) if len(rel_date) >= 4 and rel_date[:4].isdigit() else None
            poster_path = m.get("poster_path")
            poster_url = f"{TMDB_IMAGE_BASE}{poster_path}" if poster_path else None
            role_desc = m.get("character") or m.get("job")

            items.append({
                "tmdb_id": mid,
                "title": title,
                "original_title": m.get("original_title"),
                "release_year": year,
                "release_date": rel_date,
                "poster_url": poster_url,
                "character": role_desc,
                "vote_average": round(m.get("vote_average", 0), 1) if m.get("vote_average") else None,
            })

        await set_cache(cache_key, items, ttl_seconds=86400)
        return items

    async def get_person_details(
        self,
        person_id: int,
    ) -> dict[str, Any] | None:
        """Aktyor haqida to'liq ma'lumot (TMDb)."""
        if not self.api_key or not person_id:
            return None

        cache_key = f"tmdb:person_details:{person_id}"
        cached = await get_cache(cache_key)
        if cached is not None:
            return cached

        data = await self._request_with_retry(
            f"person/{person_id}",
            params={"language": "ru-RU"},
        )
        if not data:
            data = await self._request_with_retry(
                f"person/{person_id}",
                params={"language": "en-US"},
            )

        if not data:
            return None

        profile_path = data.get("profile_path")
        res = {
            "id": data.get("id"),
            "name": data.get("name"),
            "biography": data.get("biography"),
            "birthday": data.get("birthday"),
            "place_of_birth": data.get("place_of_birth"),
            "photo_url": f"{TMDB_IMAGE_BASE}{profile_path}" if profile_path else None,
            "known_for_department": data.get("known_for_department"),
        }
        await set_cache(cache_key, res, ttl_seconds=86400)
        return res


tmdb_client = TMDbClient()
