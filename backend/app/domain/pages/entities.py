from pydantic import BaseModel, ConfigDict, Field

class Page(BaseModel):
    id: int | None = None
    title: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True
    
    model_config = ConfigDict(from_attributes=True)
