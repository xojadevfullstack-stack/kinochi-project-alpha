"""
Series domain entities.
"""
from datetime import datetime
from typing import Any
from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator
from app.domain.categories.entities import Category
from app.domain.pages.entities import Page

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
    status: str = "ongoing"

class SeasonCreate(SeasonBase):
    pass

class SeasonUpdate(BaseModel):
    season_number: int | None = None
    title: str | None = None
    description: str | None = None
    poster_url: str | None = Field(None, max_length=1024)
    episode_count: int | None = None
    status: str | None = None

class Season(SeasonBase):
    id: int
    created_at: datetime
    episodes: list[Episode] = Field(default_factory=list)
    model_config = ConfigDict(from_attributes=True)


class SeriesBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    poster_url: str | None = Field(None, max_length=1024)
    trailer_url: str | None = Field(None, max_length=1024)
    imdb_rating: float | None = Field(None, ge=0, le=10)
    tmdb_id: int | None = None
    kinochi_rating: float | None = None
    kinochi_votes_count: int = 0
    release_year: int | None = None
    year: int | None = None
    director: str | None = None
    cast: str | None = None
    status: str = "ongoing"
    publish_status: str = "pending"
    is_18_plus: bool = False
    source_type: str | None = "uzmovi"
    custom_source_name: str | None = None
    custom_source_logo: str | None = None

    @model_validator(mode="before")
    @classmethod
    def sanitize_series_input(cls, data: Any) -> Any:
        if isinstance(data, dict):
            val_year = data.get("release_year") if data.get("release_year") is not None else data.get("year")
            if val_year is not None and str(val_year).strip():
                try:
                    int_year = int(str(val_year).strip())
                    data["release_year"] = int_year
                    data["year"] = int_year
                except (ValueError, TypeError):
                    pass
            for r_key in ("imdb_rating", "tmdb_rating", "kinochi_rating"):
                if data.get(r_key) is not None:
                    try:
                        r_val = str(data[r_key]).replace(",", ".").strip()
                        data[r_key] = float(r_val)
                    except (ValueError, TypeError):
                        pass
        return data

class SeriesCreate(SeriesBase):
    category_ids: list[int] | None = None
    page_ids: list[int] | None = None
    source_id: int | None = None

class SeriesUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    poster_url: str | None = Field(None, max_length=1024)
    trailer_url: str | None = Field(None, max_length=1024)
    imdb_rating: float | None = Field(None, ge=0, le=10)
    tmdb_id: int | None = None
    release_year: int | None = None
    year: int | None = None
    director: str | None = None
    cast: str | None = None
    status: str | None = None
    publish_status: str | None = None
    category_ids: list[int] | None = None
    page_ids: list[int] | None = None
    source_id: int | None = None
    is_18_plus: bool | None = None
    source_type: str | None = None
    custom_source_name: str | None = None
    custom_source_logo: str | None = None

    @model_validator(mode="before")
    @classmethod
    def sanitize_series_update(cls, data: Any) -> Any:
        if isinstance(data, dict):
            val_year = data.get("release_year") if data.get("release_year") is not None else data.get("year")
            if val_year is not None and str(val_year).strip():
                try:
                    int_year = int(str(val_year).strip())
                    data["release_year"] = int_year
                    data["year"] = int_year
                except (ValueError, TypeError):
                    pass
            for r_key in ("imdb_rating", "tmdb_rating"):
                if data.get(r_key) is not None:
                    try:
                        r_val = str(data[r_key]).replace(",", ".").strip()
                        data[r_key] = float(r_val)
                    except (ValueError, TypeError):
                        pass
        return data

from app.domain.series.source_entities import SourceResponse

class Series(SeriesBase):
    id: int
    created_at: datetime
    updated_at: datetime
    seasons: list[Season] = Field(default_factory=list)
    categories: list[Category] = Field(default_factory=list)
    pages: list['Page'] = Field(default_factory=list)
    
    source_id: int | None = None
    source: SourceResponse | None = None
    
    model_config = ConfigDict(from_attributes=True)

class SeriesSummary(SeriesBase):
    """Ro'yxat va qidiruv uchun yengil serial modeli (seasons/episodes yuklanmaydi)."""
    id: int
    created_at: datetime
    updated_at: datetime
    categories: list[Category] = Field(default_factory=list)
    pages: list['Page'] = Field(default_factory=list)
    source_id: int | None = None
    source: SourceResponse | None = None

    model_config = ConfigDict(from_attributes=True)


# Pagination responses
class PaginatedSeriesSummaryResponse(BaseModel):
    items: list[SeriesSummary]
    total: int
    page: int
    size: int
    pages: int


class PaginatedSeriesResponse(BaseModel):
    items: list[Series]
    total: int
    page: int
    size: int
    pages: int
