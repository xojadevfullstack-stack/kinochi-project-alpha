"""
Application service for managing Series (Seasons and Episodes).
"""
from typing import Sequence

from app.domain.movies.entities import Season, Episode
from app.domain.movies.series_repository import ISeriesRepository
from app.domain.movies.repository import IMovieRepository

class SeriesService:
    def __init__(self, repo: ISeriesRepository, movie_repo: IMovieRepository):
        self.repo = repo
        self.movie_repo = movie_repo

    # Seasons
    async def create_season(self, movie_id: int, season_number: int, description: str | None = None) -> Season:
        movie = await self.movie_repo.get_by_id(movie_id)
        if not movie:
            raise ValueError(f"Movie with id {movie_id} not found.")
        if not movie.is_series:
            raise ValueError("Movie is not marked as a series.")
            
        season = Season(
            movie_id=movie_id,
            season_number=season_number,
            description=description
        )
        return await self.repo.create_season(season)

    async def get_season(self, season_id: int) -> Season | None:
        return await self.repo.get_season(season_id)

    async def list_seasons(self, movie_id: int) -> Sequence[Season]:
        return await self.repo.list_seasons(movie_id)

    async def update_season(self, season_id: int, **kwargs) -> Season:
        season = await self.repo.get_season(season_id)
        if not season:
            raise ValueError(f"Season with id {season_id} not found.")
            
        for key, value in kwargs.items():
            if hasattr(season, key) and value is not None:
                setattr(season, key, value)
                
        return await self.repo.update_season(season)

    async def delete_season(self, season_id: int) -> bool:
        return await self.repo.delete_season(season_id)

    # Episodes
    async def create_episode(self, season_id: int, episode_number: int, title: str | None = None, telegram_file_id: str | None = None, storage_channel_message_id: int | None = None) -> Episode:
        season = await self.repo.get_season(season_id)
        if not season:
            raise ValueError(f"Season with id {season_id} not found.")
            
        movie = await self.movie_repo.get_by_id(season.movie_id)
        if not movie:
            raise ValueError(f"Movie not found.")
            
        # Generate code
        code = f"{movie.code}-S{season.season_number}-CH{episode_number}"
        
        episode = Episode(
            season_id=season_id,
            episode_number=episode_number,
            title=title,
            code=code,
            telegram_file_id=telegram_file_id,
            storage_channel_message_id=storage_channel_message_id
        )
        return await self.repo.create_episode(episode)

    async def get_episode(self, episode_id: int) -> Episode | None:
        return await self.repo.get_episode(episode_id)
        
    async def get_episode_by_code(self, code: str) -> Episode | None:
        return await self.repo.get_episode_by_code(code)

    async def list_episodes(self, season_id: int) -> Sequence[Episode]:
        return await self.repo.list_episodes(season_id)

    async def update_episode(self, episode_id: int, **kwargs) -> Episode:
        episode = await self.repo.get_episode(episode_id)
        if not episode:
            raise ValueError(f"Episode with id {episode_id} not found.")
            
        for key, value in kwargs.items():
            if hasattr(episode, key) and value is not None:
                setattr(episode, key, value)
                
        # If season_number or episode_number changes, code should be regenerated. 
        # But usually they shouldn't change. We'll skip complex regeneration for now.
        
        return await self.repo.update_episode(episode)

    async def delete_episode(self, episode_id: int) -> bool:
        return await self.repo.delete_episode(episode_id)
