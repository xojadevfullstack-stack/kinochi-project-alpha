from typing import List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.infrastructure.db.models.series import SeriesModel, SeasonModel, EpisodeModel
from app.infrastructure.db.models.category import CategoryModel
from app.infrastructure.db.models.translation import EpisodeTranslationModel
from app.domain.series.entities import SeriesCreate, SeriesUpdate, SeasonCreate, SeasonUpdate, EpisodeCreate, EpisodeUpdate

class SeriesRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    # --- Series ---
    async def get_all_series(self, skip: int = 0, limit: int = 100) -> Tuple[List[SeriesModel], int]:
        total_stmt = select(func.count(SeriesModel.id))
        total = await self.session.scalar(total_stmt)
        
        stmt = select(SeriesModel).options(
            selectinload(SeriesModel.seasons).selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations),
            selectinload(SeriesModel.categories)
        ).order_by(SeriesModel.id.desc()).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total or 0

    async def search_series(self, title_query: str, skip: int = 0, limit: int = 100) -> Tuple[List[SeriesModel], int]:
        search_pattern = f"%{title_query}%"
        
        total_stmt = select(func.count(SeriesModel.id)).where(SeriesModel.title.ilike(search_pattern))
        total = await self.session.scalar(total_stmt)
        
        stmt = select(SeriesModel).options(
            selectinload(SeriesModel.seasons).selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations),
            selectinload(SeriesModel.categories)
        ).where(SeriesModel.title.ilike(search_pattern)).order_by(SeriesModel.id.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        return list(result.scalars().all()), total or 0


    async def get_series_by_id(self, series_id: int) -> SeriesModel | None:
        stmt = select(SeriesModel).options(
            selectinload(SeriesModel.seasons).selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations),
            selectinload(SeriesModel.categories)
        ).where(SeriesModel.id == series_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_series_by_source(self, chat_id: int, topic_id: int | None) -> SeriesModel | None:
        stmt = select(SeriesModel).options(
            selectinload(SeriesModel.seasons).selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations),
            selectinload(SeriesModel.categories)
        ).where(SeriesModel.source_chat_id == chat_id)
        if topic_id is not None:
            stmt = stmt.where(SeriesModel.source_topic_id == topic_id)
        else:
            stmt = stmt.where(SeriesModel.source_topic_id.is_(None))
            
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_series(self, series_data: SeriesCreate) -> SeriesModel:
        series = SeriesModel(**series_data.model_dump(exclude={"category_ids", "source_link"}, exclude_unset=True))
        
        if series_data.category_ids:
            result = await self.session.execute(select(CategoryModel).where(CategoryModel.id.in_(series_data.category_ids)))
            categories = result.scalars().all()
            series.categories = list(categories)
            
        self.session.add(series)
        await self.session.flush()
        return await self.get_series_by_id(series.id)

    async def update_series(self, series_id: int, update_data: SeriesUpdate) -> SeriesModel | None:
        series = await self.get_series_by_id(series_id)
        if not series:
            return None
        
        for key, value in update_data.model_dump(exclude={"category_ids", "source_link"}, exclude_unset=True).items():
            setattr(series, key, value)
            
        if update_data.category_ids is not None:
            result = await self.session.execute(select(CategoryModel).where(CategoryModel.id.in_(update_data.category_ids)))
            categories = result.scalars().all()
            series.categories = list(categories)
            
        await self.session.flush()
        return await self.get_series_by_id(series.id)

    async def delete_series(self, series_id: int) -> bool:
        series = await self.get_series_by_id(series_id)
        if not series:
            return False
        await self.session.delete(series)
        await self.session.flush()
        return True

    # --- Seasons ---
    async def get_season_by_id(self, season_id: int) -> SeasonModel | None:
        stmt = select(SeasonModel).options(selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations)).where(SeasonModel.id == season_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
        
    async def get_seasons_by_series(self, series_id: int) -> List[SeasonModel]:
        stmt = select(SeasonModel).options(selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations)).where(SeasonModel.series_id == series_id).order_by(SeasonModel.season_number)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_season(self, season_data: SeasonCreate) -> SeasonModel:
        season = SeasonModel(**season_data.model_dump())
        self.session.add(season)
        await self.session.flush()
        return await self.get_season_by_id(season.id)

    async def update_season(self, season_id: int, update_data: SeasonUpdate) -> SeasonModel | None:
        season = await self.get_season_by_id(season_id)
        if not season:
            return None
            
        for key, value in update_data.model_dump(exclude_unset=True).items():
            setattr(season, key, value)
            
        await self.session.flush()
        return await self.get_season_by_id(season.id)
        
    async def delete_season(self, season_id: int) -> bool:
        season = await self.get_season_by_id(season_id)
        if not season:
            return False
        await self.session.delete(season)
        await self.session.flush()
        return True

    # --- Episodes ---
    async def get_episode_by_id(self, episode_id: int) -> EpisodeModel | None:
        stmt = select(EpisodeModel).options(selectinload(EpisodeModel.translations)).where(EpisodeModel.id == episode_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_episode_by_code(self, code: str) -> EpisodeModel | None:
        stmt = select(EpisodeModel).options(selectinload(EpisodeModel.translations)).where(EpisodeModel.code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_episode_with_context_by_code(self, code: str):
        """
        Bitta SQL so'rovida episode + uning season + series + barcha episodlarini yuklaydi.
        Bu get_episode_detail_by_code uchun N+1 muammosini bartaraf etadi.
        Returns: (episode, season, series) yoki (None, None, None)
        """
        # 1. Episode + translations va season_id'ni ol
        stmt = (
            select(EpisodeModel)
            .options(selectinload(EpisodeModel.translations))
            .where(EpisodeModel.code == code)
        )
        result = await self.session.execute(stmt)
        episode = result.scalar_one_or_none()
        if not episode:
            return None, None, None

        # 2. Season + uning barcha episodes (navigatsiya uchun)
        season_stmt = (
            select(SeasonModel)
            .options(
                selectinload(SeasonModel.episodes).selectinload(EpisodeModel.translations)
            )
            .where(SeasonModel.id == episode.season_id)
        )
        season_result = await self.session.execute(season_stmt)
        season = season_result.scalar_one_or_none()
        if not season:
            return episode, None, None

        # 3. Series + barcha seasons va episodes (prev/next navigatsiya uchun)
        series_stmt = (
            select(SeriesModel)
            .options(
                selectinload(SeriesModel.seasons)
                .selectinload(SeasonModel.episodes)
                .selectinload(EpisodeModel.translations),
                selectinload(SeriesModel.categories)
            )
            .where(SeriesModel.id == season.series_id)
        )
        series_result = await self.session.execute(series_stmt)
        series = series_result.scalar_one_or_none()

        return episode, season, series

    async def get_episodes_by_season(self, season_id: int) -> List[EpisodeModel]:
        stmt = select(EpisodeModel).where(EpisodeModel.season_id == season_id).order_by(EpisodeModel.episode_number)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_episode(self, episode_data: dict) -> EpisodeModel:
        episode = EpisodeModel(**episode_data)
        self.session.add(episode)
        await self.session.flush()
        return await self.get_episode_by_id(episode.id)

    async def update_episode(self, episode_id: int, update_data: EpisodeUpdate | dict) -> EpisodeModel | None:
        episode = await self.get_episode_by_id(episode_id)
        if not episode:
            return None
            
        data = update_data if isinstance(update_data, dict) else update_data.model_dump(exclude_unset=True)
        for key, value in data.items():
            setattr(episode, key, value)
            
        await self.session.flush()
        return await self.get_episode_by_id(episode.id)

    async def add_episode_translation(self, episode_id: int, language: str, telegram_file_id: str, storage_channel_message_id: int) -> EpisodeModel | None:
        translation = EpisodeTranslationModel(
            episode_id=episode_id,
            language=language,
            telegram_file_id=telegram_file_id,
            storage_channel_message_id=storage_channel_message_id
        )
        self.session.add(translation)
        await self.session.flush()
        return await self.get_episode_by_id(episode_id)

    async def delete_episode_translation(self, translation_id: int) -> bool:
        model = await self.session.get(EpisodeTranslationModel, translation_id)
        if not model:
            return False
        await self.session.delete(model)
        await self.session.flush()
        return True

    async def delete_episode(self, episode_id: int) -> bool:
        episode = await self.get_episode_by_id(episode_id)
        if not episode:
            return False
        await self.session.delete(episode)
        await self.session.flush()
        return True
