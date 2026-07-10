"""
Category domain entity.
"""
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class Category(BaseModel):
    id: int | None = None
    name: str = Field(..., min_length=1, max_length=100)
    slug: str = Field(..., min_length=1, max_length=100)
    is_active: bool = True
    created_at: datetime | None = None
    
    model_config = ConfigDict(from_attributes=True)
