"""
Series domain entities.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field, computed_field
from app.domain.categories.entities import Category

class EpisodeBase(BaseModel):
    season_id: int
    episode_number: int
    title: str | None = None
    duration: int | None = None # In minutes

class EpisodeCreate(EpisodeBase):
    pass

class EpisodeUpdate(BaseModel):
    title: str | None = None
    episode_number: int | None = None
    duration: int | None = None

class Episode(EpisodeBase):
    id: int
    code: str
    display_code: str
    created_at: datetime
    translations: list['EpisodeTranslation'] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

class EpisodeDetail(Episode):
    prev_episode_code: str | None = None
    next_episode_code: str | None = None
    series_title: str | None = None
    season_number: int | None = None
    season_description: str | None = None
    series_id: int | None = None

class EpisodeTranslation(BaseModel):
    id: int | None = None
    episode_id: int
    language: str
    telegram_file_id: str | None = None
    storage_channel_message_id: int | None = None
    created_at: datetime | None = None
    
    model_config = ConfigDict(from_attributes=True)

class SeasonBase(BaseModel):
    series_id: int
    season_number: int
    title: str | None = None
    description: str | None = None
    poster_url: str | None = Field(None, max_length=1024)
    episode_count: int | None = None

class SeasonCreate(SeasonBase):
    pass

class SeasonUpdate(BaseModel):
    season_number: int | None = None
    title: str | None = None
    description: str | None = None
    poster_url: str | None = Field(None, max_length=1024)
    episode_count: int | None = None

class Season(SeasonBase):
    id: int
    created_at: datetime
    episodes: list[Episode] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class SeriesBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    poster_url: str | None = Field(None, max_length=1024)
    imdb_rating: float | None = Field(None, ge=0, le=10)
    release_year: int | None = None
    director: str | None = None
    cast: str | None = None

class SeriesCreate(SeriesBase):
    category_ids: list[int] | None = None
    source_id: int | None = None

class SeriesUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    poster_url: str | None = Field(None, max_length=1024)
    imdb_rating: float | None = Field(None, ge=0, le=10)
    release_year: int | None = None
    director: str | None = None
    cast: str | None = None
    category_ids: list[int] | None = None
    source_id: int | None = None

from app.domain.series.source_entities import SourceResponse

class Series(SeriesBase):
    id: int
    created_at: datetime
    updated_at: datetime
    seasons: list[Season] = Field(default_factory=list)
    categories: list[Category] = Field(default_factory=list)
    
    source_id: int | None = None
    source: SourceResponse | None = None
    
    model_config = ConfigDict(from_attributes=True)

# Pagination responses
class PaginatedSeriesResponse(BaseModel):
    items: list[Series]
    total: int
    page: int
    size: int
    pages: int
