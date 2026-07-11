"""
Series domain entities.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class EpisodeBase(BaseModel):
    season_id: int
    episode_number: int
    title: str | None = None
    telegram_file_id: str | None = None
    storage_channel_message_id: int | None = None

class EpisodeCreate(EpisodeBase):
    pass

class EpisodeUpdate(BaseModel):
    title: str | None = None
    episode_number: int | None = None

class Episode(EpisodeBase):
    id: int
    code: str
    display_code: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class EpisodeDetail(Episode):
    prev_episode_code: str | None = None
    next_episode_code: str | None = None
    series_title: str | None = None
    season_number: int | None = None
    season_description: str | None = None
    series_id: int | None = None


class SeasonBase(BaseModel):
    series_id: int
    season_number: int
    title: str | None = None
    description: str | None = None

class SeasonCreate(SeasonBase):
    pass

class SeasonUpdate(BaseModel):
    season_number: int | None = None
    title: str | None = None
    description: str | None = None

class Season(SeasonBase):
    id: int
    created_at: datetime
    episodes: list[Episode] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class SeriesBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    poster_url: str | None = Field(None, max_length=1024)

class SeriesCreate(SeriesBase):
    pass

class SeriesUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    poster_url: str | None = Field(None, max_length=1024)

class Series(SeriesBase):
    id: int
    created_at: datetime
    updated_at: datetime
    seasons: list[Season] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)

# Pagination responses
class PaginatedSeriesResponse(BaseModel):
    items: list[Series]
    total: int
    page: int
    size: int
    pages: int
