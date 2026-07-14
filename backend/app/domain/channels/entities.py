"""MandatoryChannel domain entity."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class MandatoryChannel(BaseModel):
    id: int | None = None
    channel_id: int | None = None
    channel_username: str | None = None
    channel_title: str | None = None
    is_active: bool = True
    subscriber_limit: int | None = None
    current_subscriber_count: int = 0
    added_at: datetime | None = None
    
    model_config = ConfigDict(from_attributes=True)
