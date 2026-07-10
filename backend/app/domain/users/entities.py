"""User domain entity."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class User(BaseModel):
    id: int | None = None
    telegram_id: int = Field(...)
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_admin: bool = False
    is_banned: bool = False
    joined_at: datetime | None = None
    last_active_at: datetime | None = None
    
    model_config = ConfigDict(from_attributes=True)
