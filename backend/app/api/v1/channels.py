"""API v1 — Channels endpoints."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import get_channel_service, get_current_admin
from app.application.channels.service import ChannelService

router = APIRouter(prefix="/channels", tags=["channels"])

class ChannelCreate(BaseModel):
    channel_id: int | None = None
    channel_username: str | None = None
    channel_title: str | None = None
    is_active: bool = True

class ChannelUpdate(BaseModel):
    channel_username: str | None = None
    channel_title: str | None = None
    is_active: bool | None = None

class ChannelResponse(BaseModel):
    id: int
    channel_id: int | None = None
    channel_username: str | None = None
    channel_title: str | None = None
    is_active: bool
    added_at: datetime

    model_config = {"from_attributes": True}

class PaginatedChannelsResponse(BaseModel):
    items: list[ChannelResponse]
    total: int

@router.post("", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    channel_in: ChannelCreate,
    service: ChannelService = Depends(get_channel_service),
    admin: dict = Depends(get_current_admin)
):
    """Create a new mandatory channel (Admin only)."""
    return await service.create_channel(**channel_in.model_dump())

@router.get("", response_model=PaginatedChannelsResponse)
async def list_channels(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: ChannelService = Depends(get_channel_service),
    admin: dict = Depends(get_current_admin)
):
    """List all mandatory channels (Admin only)."""
    channels, total = await service.list_all(skip=skip, limit=limit)
    return {"items": channels, "total": total}

@router.get("/active", response_model=list[ChannelResponse])
async def list_active_channels(
    service: ChannelService = Depends(get_channel_service)
):
    """List active mandatory channels (Public / used by bot)."""
    return await service.list_active()

@router.get("/{channel_id}", response_model=ChannelResponse)
async def get_channel(
    channel_id: int,
    service: ChannelService = Depends(get_channel_service),
    admin: dict = Depends(get_current_admin)
):
    """Get channel by DB ID (Admin only)."""
    channel = await service.get_channel(channel_id)
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel

@router.put("/{channel_id}", response_model=ChannelResponse)
async def update_channel(
    channel_id: int,
    channel_in: ChannelUpdate,
    service: ChannelService = Depends(get_channel_service),
    admin: dict = Depends(get_current_admin)
):
    """Update a channel (Admin only)."""
    channel = await service.update_channel(id=channel_id, **channel_in.model_dump(exclude_unset=True))
    if not channel:
        raise HTTPException(status_code=404, detail="Channel not found")
    return channel

@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: int,
    service: ChannelService = Depends(get_channel_service),
    admin: dict = Depends(get_current_admin)
):
    """Delete a channel (Admin only)."""
    success = await service.delete_channel(channel_id)
    if not success:
        raise HTTPException(status_code=404, detail="Channel not found")
