from pydantic import BaseModel, Field
from datetime import datetime

class SourceCreate(BaseModel):
    name: str
    type: str = Field(pattern="^(kanal|superguruh)$")
    chat_id: int
    topic_id: int | None = None

class SourceUpdate(BaseModel):
    name: str | None = None
    type: str | None = Field(None, pattern="^(kanal|superguruh)$")
    chat_id: int | None = None
    topic_id: int | None = None

class SourceResponse(BaseModel):
    id: int
    name: str
    type: str
    chat_id: int
    topic_id: int | None = None
    created_at: datetime

    class Config:
        from_attributes = True
