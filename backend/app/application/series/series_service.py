import shortuuid
from typing import Tuple, List
from fastapi import UploadFile, HTTPException

from app.domain.series.entities import (
    Series, SeriesCreate, SeriesUpdate,
    Season, SeasonCreate, SeasonUpdate,
    Episode, EpisodeCreate, EpisodeUpdate, EpisodeDetail
)
from app.infrastructure.db.repositories.series_repository import SeriesRepository
from app.infrastructure.telegram.telegram_client import TelegramClient

class SeriesService:
    def __init__(self, repository: SeriesRepository, telegram_api: TelegramClient):
        self.repository = repository
        self.telegram_api = telegram_api

    def _generate_code(self) -> str:
        # shortuuid with default alphabet is URL safe
        # Generating a unique 8-character code similar to movies
        return shortuuid.uuid()[:8]

    # --- Series ---
    async def get_all_series(self, skip: int = 0, limit: int = 100) -> Tuple[List[Series], int]:
        series_models, total = await self.repository.get_all_series(skip, limit)
        return [Series.model_validate(s) for s in series_models], total

    async def search_series(self, title_query: str, skip: int = 0, limit: int = 100) -> Tuple[List[Series], int]:
        series_models, total = await self.repository.search_series(title_query, skip, limit)
        return [Series.model_validate(s) for s in series_models], total

    async def get_series_by_id(self, series_id: int) -> Series | None:
        series_model = await self.repository.get_series_by_id(series_id)
        if not series_model:
            return None
        return Series.model_validate(series_model)

    async def get_series_by_source(self, chat_id: int, topic_id: int | None) -> Series | None:
        series_model = await self.repository.get_series_by_source(chat_id, topic_id)
        if not series_model:
            return None
        return Series.model_validate(series_model)

    async def create_series(self, series_data: SeriesCreate | dict) -> Series:
        series_model = await self.repository.create_series(series_data)
        return Series.model_validate(series_model)

    async def update_series(self, series_id: int, update_data: SeriesUpdate) -> Series | None:
        series_model = await self.repository.update_series(series_id, update_data)
        if not series_model:
            return None
        return Series.model_validate(series_model)

    async def delete_series(self, series_id: int) -> bool:
        return await self.repository.delete_series(series_id)

    # --- Seasons ---
    async def get_season_by_id(self, season_id: int) -> Season | None:
        season_model = await self.repository.get_season_by_id(season_id)
        if not season_model:
            return None
        return Season.model_validate(season_model)

    async def create_season(self, season_data: SeasonCreate) -> Season:
        # Check if series exists
        series = await self.get_series_by_id(season_data.series_id)
        if not series:
            raise ValueError(f"Series with ID {season_data.series_id} not found")
            
        season_model = await self.repository.create_season(season_data)
        return Season.model_validate(season_model)

    async def update_season(self, season_id: int, update_data: SeasonUpdate) -> Season | None:
        season_model = await self.repository.update_season(season_id, update_data)
        if not season_model:
            return None
        return Season.model_validate(season_model)

    async def delete_season(self, season_id: int) -> bool:
        return await self.repository.delete_season(season_id)

    # --- Episodes ---
    async def get_episode_by_id(self, episode_id: int) -> Episode | None:
        episode_model = await self.repository.get_episode_by_id(episode_id)
        if not episode_model:
            return None
        return Episode.model_validate(episode_model)
        
    async def get_episode_by_code(self, code: str) -> Episode | None:
        episode_model = await self.repository.get_episode_by_code(code)
        if not episode_model:
            return None
        return Episode.model_validate(episode_model)

    async def get_episode_detail_by_code(self, code: str) -> EpisodeDetail | None:
        # Repository'dagi optimallashtirilgan metod — 3 ta alohida so'rov o'rniga bitta
        episode_model, season_model, series_model = await self.repository.get_episode_with_context_by_code(code)

        if not episode_model:
            return None
        if not season_model or not series_model:
            return None

        episode = Episode.model_validate(episode_model)
        season = Season.model_validate(season_model)
        series = Series.model_validate(series_model)

        # Flatten episodes from all seasons to find prev/next
        sorted_seasons = sorted(series.seasons, key=lambda s: s.season_number)

        all_episodes = []
        for s in sorted_seasons:
            sorted_eps = sorted(s.episodes, key=lambda e: e.episode_number)
            all_episodes.extend(sorted_eps)

        idx = next((i for i, e in enumerate(all_episodes) if e.id == episode.id), -1)

        prev_code = None
        next_code = None

        if idx > 0:
            prev_code = all_episodes[idx - 1].code
        if idx != -1 and idx < len(all_episodes) - 1:
            next_code = all_episodes[idx + 1].code

        return EpisodeDetail(
            **episode.model_dump(),
            prev_episode_code=prev_code,
            next_episode_code=next_code,
            series_title=series.title,
            season_number=season.season_number,
            season_description=season.description,
            series_id=series.id
        )


    async def create_episode(self, episode_data: EpisodeCreate) -> Episode:
        # Check if season exists
        season = await self.repository.get_season_by_id(episode_data.season_id)
        if not season:
            raise ValueError(f"Season with ID {episode_data.season_id} not found")
            
        # Generate internal code and display code
        code = self._generate_code()
        display_code = f"S{season.season_number}-CH{episode_data.episode_number}"
        
        data_dict = episode_data.model_dump()
        data_dict["code"] = code
        data_dict["display_code"] = display_code
        
        episode_model = await self.repository.create_episode(data_dict)
        return Episode.model_validate(episode_model)

    async def update_episode(self, episode_id: int, update_data: EpisodeUpdate) -> Episode | None:
        episode_model = await self.repository.get_episode_by_id(episode_id)
        if not episode_model:
            return None
            
        update_dict = update_data.model_dump(exclude_unset=True)
        if update_data.episode_number is not None and update_data.episode_number != episode_model.episode_number:
            season = await self.repository.get_season_by_id(episode_model.season_id)
            if season:
                update_dict["display_code"] = f"S{season.season_number}-CH{update_data.episode_number}"
                
        # Repozitoriy endi dict qabul qila oladi va barcha yangilanishlar bitta chaqiruvda bajariladi
        updated_model = await self.repository.update_episode(episode_id, update_dict)
        return Episode.model_validate(updated_model)

    async def delete_episode(self, episode_id: int) -> bool:
        return await self.repository.delete_episode(episode_id)

    async def upload_episode_video(self, episode_id: int, file: UploadFile, language: str = "Asosiy") -> Episode | None:
        episode = await self.repository.get_episode_by_id(episode_id)
        if not episode:
            return None
            
        file_bytes = await file.read()
        
        # Send to Telegram
        file_id, message_id = await self.telegram_api.send_video_to_storage(
            file_bytes=file_bytes,
            filename=file.filename or "video.mp4",
            mime_type=file.content_type or "video/mp4"
        )
        
        updated_episode = await self.repository.add_episode_translation(
            episode_id=episode_id,
            language=language,
            telegram_file_id=file_id,
            storage_channel_message_id=message_id
        )
        
        return Episode.model_validate(updated_episode)

    async def link_episode_video_from_message(self, episode_id: int, message_id: int, language: str = "Asosiy") -> Episode | None:
        episode = await self.repository.get_episode_by_id(episode_id)
        if not episode:
            return None
            
        # Get file_id from telegram message
        file_id = await self.telegram_api.get_video_file_id_from_message(message_id)
        
        updated_episode = await self.repository.add_episode_translation(
            episode_id=episode_id,
            language=language,
            telegram_file_id=file_id,
            storage_channel_message_id=message_id
        )
        
        return Episode.model_validate(updated_episode)

    async def delete_episode_translation(self, translation_id: int) -> bool:
        return await self.repository.delete_episode_translation(translation_id)

