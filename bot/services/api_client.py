import httpx
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
            print(f"Error registering user: {e}")
            return {}

    async def get_movie_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.get(f"/movies/code/{code}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching movie {code}: {e}")
            return None

    async def get_movie_by_id(self, movie_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.get(f"/movies/{movie_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching movie by ID {movie_id}: {e}")
            return None

    async def get_episode_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.get(f"/series/episodes/code/{code}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching episode {code}: {e}")
            return None

    async def get_series_by_id(self, series_id: int) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.get(f"/series/{series_id}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching series {series_id}: {e}")
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
            print(f"Error fetching series by source {chat_id}/{topic_id}: {e}")
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
            print(f"Error creating episode {episode_number} for season {season_id}: {e}")
            return None

    async def get_active_channels(self) -> list[Dict[str, Any]]:
        try:
            response = await self.client.get("/channels/active")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching active channels: {e}")
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
            print(f"Error verifying subscription for channel {channel_id}: {e}")
            return False

    async def get_movies(self, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
        try:
            response = await self.client.get("/movies", params={"skip": skip, "limit": limit})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching movies: {e}")
            return {"items": [], "total": 0}

    async def get_series(self, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
        try:
            response = await self.client.get("/series", params={"skip": skip, "limit": limit})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching series: {e}")
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
            print(f"Error searching movies with query '{query}': {e}")
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
            print(f"Error searching series with query '{query}': {e}")
            return {"items": [], "total": 0}

api_client = APIClient()
