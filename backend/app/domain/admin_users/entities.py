"""AdminUser domain entity — BUTUNLAY User (Telegram) jadvalidan alohida."""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class AdminUser(BaseModel):
    id: int | None = None
    email: str = Field(..., max_length=255)
    hashed_password: str = Field(..., max_length=255)
    is_active: bool = True
    role: str = Field(default="superadmin", max_length=50)
    created_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
