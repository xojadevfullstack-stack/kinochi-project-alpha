from enum import Enum
from datetime import datetime
from pydantic import BaseModel, ConfigDict

class BroadcastStatus(str, Enum):
    DRAFT = "draft"
    SENDING = "sending"
    COMPLETED = "completed"
    FAILED = "failed"

class Broadcast(BaseModel):
    id: int | None = None
    message_text: str
    status: BroadcastStatus = BroadcastStatus.DRAFT
    media_type: str = "text"
    media_url: str | None = None
    button_text: str | None = None
    button_url: str | None = None
    total_recipients: int = 0
    sent_count: int = 0
    failed_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
