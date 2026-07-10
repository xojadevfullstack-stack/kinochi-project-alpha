from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class BroadcastStatus(str, Enum):
    DRAFT = "draft"
    SENDING = "sending"
    COMPLETED = "completed"
    FAILED = "failed"

class Broadcast(BaseModel):
    id: int | None = None
    message_text: str
    status: BroadcastStatus = BroadcastStatus.DRAFT
    total_recipients: int = 0
    sent_count: int = 0
    failed_count: int = 0
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
