"""
Pydantic schemas for Series (Seasons and Episodes).
"""
from pydantic import BaseModel, Field

# --- Seasons ---
class SeasonCreate(BaseModel):
    season_number: int
    description: str | None = None

class SeasonUpdate(BaseModel):
    season_number: int | None = None
    description: str | None = None

class SeasonResponse(BaseModel):
    id: int
    movie_id: int
    season_number: int
    description: str | None = None

    class Config:
        from_attributes = True

# --- Episodes ---
class EpisodeCreate(BaseModel):
    episode_number: int
    title: str | None = None
    telegram_file_id: str | None = None
    storage_channel_message_id: int | None = None

class EpisodeUpdate(BaseModel):
    episode_number: int | None = None
    title: str | None = None
    telegram_file_id: str | None = None
    storage_channel_message_id: int | None = None

class EpisodeResponse(BaseModel):
    id: int
    season_id: int
    episode_number: int
    title: str | None = None
    code: str
    telegram_file_id: str | None = None
    storage_channel_message_id: int | None = None

    class Config:
        from_attributes = True
