"""
Concrete implementation of ISeriesRepository.
"""
from typing import Sequence
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.movies.entities import Season, Episode
from app.domain.movies.series_repository import ISeriesRepository
from app.infrastructure.db.models.series import SeasonModel, EpisodeModel


class SeriesRepositoryImpl(ISeriesRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    # Seasons
    def _to_domain_season(self, model: SeasonModel) -> Season:
        return Season.model_validate(model)

    async def create_season(self, season: Season) -> Season:
        model = SeasonModel(**season.model_dump(exclude={"id", "created_at", "episodes"}, exclude_unset=True))
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain_season(model)

    async def get_season(self, season_id: int) -> Season | None:
        model = await self.session.get(SeasonModel, season_id)
        return self._to_domain_season(model) if model else None

    async def list_seasons(self, movie_id: int) -> Sequence[Season]:
        result = await self.session.execute(
            select(SeasonModel)
            .where(SeasonModel.movie_id == movie_id)
            .order_by(SeasonModel.season_number)
        )
        models = result.scalars().all()
        return [self._to_domain_season(m) for m in models]

    async def update_season(self, season: Season) -> Season:
        model = await self.session.get(SeasonModel, season.id)
        if not model:
            raise ValueError(f"Season with id {season.id} not found")
            
        update_data = season.model_dump(exclude={"id", "created_at", "episodes"}, exclude_unset=True)
        for key, value in update_data.items():
            setattr(model, key, value)
            
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain_season(model)

    async def delete_season(self, season_id: int) -> bool:
        model = await self.session.get(SeasonModel, season_id)
        if not model:
            return False
        await self.session.delete(model)
        await self.session.flush()
        return True

    # Episodes
    def _to_domain_episode(self, model: EpisodeModel) -> Episode:
        return Episode.model_validate(model)

    async def create_episode(self, episode: Episode) -> Episode:
        model = EpisodeModel(**episode.model_dump(exclude={"id", "created_at"}, exclude_unset=True))
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain_episode(model)

    async def get_episode(self, episode_id: int) -> Episode | None:
        model = await self.session.get(EpisodeModel, episode_id)
        return self._to_domain_episode(model) if model else None

    async def get_episode_by_code(self, code: str) -> Episode | None:
        result = await self.session.execute(select(EpisodeModel).where(EpisodeModel.code == code))
        model = result.scalar_one_or_none()
        return self._to_domain_episode(model) if model else None

    async def list_episodes(self, season_id: int) -> Sequence[Episode]:
        result = await self.session.execute(
            select(EpisodeModel)
            .where(EpisodeModel.season_id == season_id)
            .order_by(EpisodeModel.episode_number)
        )
        models = result.scalars().all()
        return [self._to_domain_episode(m) for m in models]

    async def update_episode(self, episode: Episode) -> Episode:
        model = await self.session.get(EpisodeModel, episode.id)
        if not model:
            raise ValueError(f"Episode with id {episode.id} not found")
            
        update_data = episode.model_dump(exclude={"id", "created_at"}, exclude_unset=True)
        for key, value in update_data.items():
            setattr(model, key, value)
            
        await self.session.flush()
        await self.session.refresh(model)
        return self._to_domain_episode(model)

    async def delete_episode(self, episode_id: int) -> bool:
        model = await self.session.get(EpisodeModel, episode_id)
        if not model:
            return False
        await self.session.delete(model)
        await self.session.flush()
        return True
