import logging
import httpx

logger = logging.getLogger(__name__)
from typing import Optional, Dict, Any
from config import settings

class APIClient:
    def __init__(self):
        self.base_url = settings.BACKEND_API_URL.rstrip('/')
        # X-Bot-Secret header — backend /users/register himoyasi uchun
        headers = {}
        if settings.BOT_API_SECRET:
            headers["X-Bot-Secret"] = settings.BOT_API_SECRET
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0, headers=headers)

    async def close(self):
        await self.client.aclose()

    async def register_user(self, telegram_id: int, username: Optional[str], first_name: Optional[str], last_name: Optional[str]) -> Dict[str, Any]:
        payload = {
            "telegram_id": telegram_id,
            "username": username,
            "first_name": first_name,
            "last_name": last_name
        }
        try:
            response = await self.client.post("/users/register", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error registering user: {e}")
            return {}

    async def get_movie_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        clean_code = str(code).strip()
        try:
            response = await self.client.get(f"/movies/code/{clean_code}")
            if response.status_code == 404:
                if clean_code.isdigit():
                    return await self.get_movie_by_id(int(clean_code))
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching movie {code}: {e}")
            if clean_code.isdigit():
                return await self.get_movie_by_id(int(clean_code))
            return None

    async def get_movie_by_id(self, movie_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.get(f"/movies/{movie_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching movie by ID {movie_id}: {e}")
            return None

    async def get_episode_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        clean_code = str(code).strip()
        try:
            response = await self.client.get(f"/series/episodes/code/{clean_code}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching episode {code}: {e}")
            return None

    async def get_series_by_id(self, series_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.get(f"/series/{series_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching series {series_id}: {e}")
            return None

    async def get_series_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        clean_code = str(code).strip()
        # Direct check if it's numeric or s_id / s{id} / series_{id} / serial_{id}
        if clean_code.isdigit():
            return await self.get_series_by_id(int(clean_code))
        lower_code = clean_code.lower()
        if lower_code.startswith("s_") and lower_code[2:].isdigit():
            return await self.get_series_by_id(int(lower_code[2:]))
        if lower_code.startswith("s") and lower_code[1:].isdigit():
            return await self.get_series_by_id(int(lower_code[1:]))
        if lower_code.startswith("series_") and lower_code[7:].isdigit():
            return await self.get_series_by_id(int(lower_code[7:]))
        if lower_code.startswith("serial_") and lower_code[7:].isdigit():
            return await self.get_series_by_id(int(lower_code[7:]))

        try:
            response = await self.client.get(f"/series/code/{clean_code}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching series by code {code}: {e}")
            return None


    async def get_series_by_source(self, chat_id: int, topic_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        try:
            params = {"chat_id": chat_id}
            if topic_id is not None:
                params["topic_id"] = topic_id
            response = await self.client.get("/series/by-source", params=params)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching series by source {chat_id}/{topic_id}: {e}")
            return None

    async def create_episode(self, season_id: int, episode_number: int, title: Optional[str] = None) -> Optional[Dict[str, Any]]:
        payload = {
            "season_id": season_id,
            "episode_number": episode_number
        }
        if title:
            payload["title"] = title
            
        try:
            response = await self.client.post(f"/series/seasons/{season_id}/episodes", json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error creating episode {episode_number} for season {season_id}: {e}")
            return None

    async def reserve_episodes(self, season_id: int, items: list[dict]) -> Optional[list[dict]]:
        try:
            response = await self.client.post(
                f"/series/seasons/{season_id}/reserve-episodes",
                json={"items": items}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error reserving episodes for season {season_id}: {e}")
            return None


    async def get_active_channels(self) -> list[Dict[str, Any]]:
        try:
            response = await self.client.get("/channels/active")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching active channels: {e}")
            return []

    async def verify_channel_subscription(self, channel_id: int, user_id: int) -> bool:
        try:
            response = await self.client.post(
                f"/channels/{channel_id}/verify-subscriber",
                json={"user_id": user_id}
            )
            response.raise_for_status()
            data = response.json()
            return data.get("success", False)
        except httpx.HTTPError as e:
            logger.error(f"Error verifying subscription for channel {channel_id}: {e}")
            return False

    async def get_movies(self, skip: int = 0, limit: int = 10, page_id: Optional[int] = None) -> Dict[str, Any]:
        try:
            params = {"skip": skip, "limit": limit}
            if page_id:
                params["page_id"] = page_id
            response = await self.client.get("/movies", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching movies: {e}")
            return {"items": [], "total": 0}

    async def get_series(self, skip: int = 0, limit: int = 10, page_id: Optional[int] = None) -> Dict[str, Any]:
        try:
            params = {"skip": skip, "limit": limit}
            if page_id:
                params["page_id"] = page_id
            response = await self.client.get("/series", params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching series: {e}")
            return {"items": [], "total": 0}

    async def search_movies(self, query: str, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
        try:
            response = await self.client.get(
                "/movies/search",
                params={"q": query, "skip": skip, "limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error searching movies with query '{query}': {e}")
            return {"items": [], "total": 0}

    async def search_series(self, query: str, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
        try:
            response = await self.client.get(
                "/series/search",
                params={"q": query, "skip": skip, "limit": limit}
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error searching series with query '{query}': {e}")
            return {"items": [], "total": 0}

    async def get_pages(self, skip: int = 0, limit: int = 100) -> Dict[str, Any]:
        try:
            response = await self.client.get("/pages", params={"skip": skip, "limit": limit})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Error fetching pages: {e}")
            return {"items": [], "total": 0}

    async def generate_login_token(self, telegram_id: int, first_name: Optional[str] = None, username: Optional[str] = None) -> Optional[str]:
        """
        Requests an access_token from /auth/dev-login.
        First tries internal configured client, then falls back to public Render backend if needed.
        """
        payload = {
            "telegram_id": telegram_id,
            "first_name": first_name or "Foydalanuvchi",
            "username": username or "user"
        }
        
        # 1. Try via self.client
        try:
            response = await self.client.post("/auth/dev-login", json=payload)
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token")
                if token:
                    return token
            logger.warning(f"Internal /auth/dev-login returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.warning(f"Internal /auth/dev-login failed: {e}. Trying public fallback...")

        # 2. Fallback via public Render backend directly
        public_url = "https://kinochi-project-alpha.onrender.com/api/v1/auth/dev-login"
        try:
            async with httpx.AsyncClient(timeout=10.0) as fallback_client:
                response = await fallback_client.post(public_url, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("access_token")
                logger.error(f"Fallback /auth/dev-login returned status {response.status_code}: {response.text}")
        except Exception as e:
            logger.error(f"Fallback /auth/dev-login failed: {e}")

        return None

api_client = APIClient()
