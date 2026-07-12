"""
Movie domain entity.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

from app.domain.categories.entities import Category


class Movie(BaseModel):
    id: int | None = None
    title: str = Field(..., min_length=1, max_length=255)
    original_title: str | None = Field(None, max_length=255)
    description: str | None = None
    imdb_rating: float | None = Field(None, ge=0, le=10)
    tmdb_rating: float | None = Field(None, ge=0, le=10)
    genres: str | None = None # Comma-separated string or list, keeping simple for now
    cast: str | None = None
    director: str | None = None
    release_year: int | None = None
    runtime: int | None = None # In minutes
    poster_url: str | None = None
    trailer_url: str | None = None
    code: str = Field(..., min_length=1, max_length=50) # Unique code
    
    translations: list['MovieTranslation'] = Field(default_factory=list)
    
    created_at: datetime | None = None
    updated_at: datetime | None = None
    
    categories: list[Category] = Field(default_factory=list)
    
    model_config = ConfigDict(from_attributes=True)

class MovieTranslation(BaseModel):
    id: int | None = None
    movie_id: int
    language: str
    telegram_file_id: str | None = None
    storage_channel_message_id: int | None = None
    created_at: datetime | None = None
    
    model_config = ConfigDict(from_attributes=True)
