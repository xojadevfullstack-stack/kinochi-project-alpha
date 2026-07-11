import httpx
from typing import Optional, Dict, Any
from config import settings

class APIClient:
    def __init__(self):
        self.base_url = settings.BACKEND_API_URL.rstrip('/')
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)

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

    async def get_active_channels(self) -> list[Dict[str, Any]]:
        try:
            response = await self.client.get("/channels/active")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching active channels: {e}")
            return []

    async def search_movies(self, query: str, skip: int = 0, limit: int = 10) -> Dict[str, Any]:
        try:
            response = await self.client.get(f"/movies/search?q={query}&skip={skip}&limit={limit}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error searching movies with query '{query}': {e}")
            return {"items": [], "total": 0}

    async def get_episode_by_code(self, code: str) -> Optional[Dict[str, Any]]:
        # This requires an endpoint on backend. Wait, did I add GET /series/episodes/code/{code}?
        # I only added get_episode_by_code in service but not in router!
        # I need to add that router in backend first.
        # But wait, let's assume I will add it next.
        try:
            response = await self.client.get(f"/series/episodes/code/{code}")
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching episode {code}: {e}")
            return None

    async def update_movie_video(self, movie_id: int, file_id: str, message_id: int) -> bool:
        try:
            payload = {"telegram_file_id": file_id, "storage_channel_message_id": message_id}
            response = await self.client.put(f"/movies/{movie_id}", json=payload)
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            print(f"Error updating movie {movie_id} video: {e}")
            return False

    async def update_episode_video(self, episode_id: int, file_id: str, message_id: int) -> bool:
        try:
            payload = {"telegram_file_id": file_id, "storage_channel_message_id": message_id}
            response = await self.client.put(f"/series/episodes/{episode_id}", json=payload)
            response.raise_for_status()
            return True
        except httpx.HTTPError as e:
            print(f"Error updating episode {episode_id} video: {e}")
            return False

    async def get_seasons(self, movie_id: int) -> list:
        try:
            response = await self.client.get(f"/series/movies/{movie_id}/seasons")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching seasons for movie {movie_id}: {e}")
            return []

    async def get_episodes(self, season_id: int) -> list:
        try:
            response = await self.client.get(f"/series/seasons/{season_id}/episodes")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            print(f"Error fetching episodes for season {season_id}: {e}")
            return []

api_client = APIClient()
