"""
Series (Seasons and Episodes) repository interface.
"""
from abc import ABC, abstractmethod
from typing import Sequence

from app.domain.movies.entities import Season, Episode


class ISeriesRepository(ABC):
    # Seasons
    @abstractmethod
    async def create_season(self, season: Season) -> Season:
        pass

    @abstractmethod
    async def get_season(self, season_id: int) -> Season | None:
        pass
        
    @abstractmethod
    async def list_seasons(self, movie_id: int) -> Sequence[Season]:
        pass

    @abstractmethod
    async def update_season(self, season: Season) -> Season:
        pass

    @abstractmethod
    async def delete_season(self, season_id: int) -> bool:
        pass

    # Episodes
    @abstractmethod
    async def create_episode(self, episode: Episode) -> Episode:
        pass

    @abstractmethod
    async def get_episode(self, episode_id: int) -> Episode | None:
        pass
        
    @abstractmethod
    async def get_episode_by_code(self, code: str) -> Episode | None:
        pass

    @abstractmethod
    async def list_episodes(self, season_id: int) -> Sequence[Episode]:
        pass

    @abstractmethod
    async def update_episode(self, episode: Episode) -> Episode:
        pass

    @abstractmethod
    async def delete_episode(self, episode_id: int) -> bool:
        pass
