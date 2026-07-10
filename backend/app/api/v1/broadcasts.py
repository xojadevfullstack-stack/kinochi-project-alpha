"""API v1 — Broadcasts endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from pydantic import BaseModel
from typing import Sequence
from datetime import datetime

from app.api.deps import get_broadcast_service, get_current_admin
from app.application.broadcasts.service import BroadcastService
from app.domain.broadcasts.entities import BroadcastStatus

router = APIRouter(prefix="/broadcasts", tags=["broadcasts"])

class BroadcastCreate(BaseModel):
    message_text: str

class BroadcastTestRequest(BaseModel):
    test_telegram_id: int

class BroadcastResponse(BaseModel):
    id: int
    message_text: str
    status: BroadcastStatus
    total_recipients: int
    sent_count: int
    failed_count: int
    created_at: datetime | None = None
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}

class PaginatedBroadcastsResponse(BaseModel):
    items: list[BroadcastResponse]
    total: int


@router.post("", response_model=BroadcastResponse, status_code=status.HTTP_201_CREATED)
async def create_broadcast(
    data: BroadcastCreate,
    service: BroadcastService = Depends(get_broadcast_service),
    admin: dict = Depends(get_current_admin)
):
    """Create a new broadcast in DRAFT status (Admin only)."""
    return await service.create_broadcast(message_text=data.message_text)


@router.get("", response_model=PaginatedBroadcastsResponse)
async def list_broadcasts(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: BroadcastService = Depends(get_broadcast_service),
    admin: dict = Depends(get_current_admin)
):
    """List broadcasts (Admin only)."""
    broadcasts, total = await service.list_broadcasts(skip=skip, limit=limit)
    return {"items": broadcasts, "total": total}


@router.get("/{broadcast_id}", response_model=BroadcastResponse)
async def get_broadcast(
    broadcast_id: int,
    service: BroadcastService = Depends(get_broadcast_service),
    admin: dict = Depends(get_current_admin)
):
    """Get single broadcast status (Admin only)."""
    broadcast = await service.get_broadcast(broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")
    return broadcast


@router.post("/{broadcast_id}/send", status_code=status.HTTP_202_ACCEPTED)
async def start_broadcast(
    broadcast_id: int,
    background_tasks: BackgroundTasks,
    service: BroadcastService = Depends(get_broadcast_service),
    admin: dict = Depends(get_current_admin)
):
    """Start sending broadcast in background (Admin only)."""
    broadcast = await service.start_broadcast(broadcast_id, background_tasks)
    if not broadcast:
        raise HTTPException(status_code=400, detail="Broadcast not found or already sent/sending")
        
    return {"status": "accepted", "message": "Broadcast sending started in background"}


@router.post("/{broadcast_id}/test", status_code=status.HTTP_200_OK)
async def test_broadcast(
    broadcast_id: int,
    data: BroadcastTestRequest,
    service: BroadcastService = Depends(get_broadcast_service),
    admin: dict = Depends(get_current_admin)
):
    """Test send broadcast to a specific telegram ID (Admin only)."""
    from app.infrastructure.telegram.telegram_client import telegram_client

    broadcast = await service.get_broadcast(broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")
        
    success = await telegram_client.send_message(chat_id=data.test_telegram_id, text=broadcast.message_text)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send test message via Telegram API")
        
    return {"status": "success", "message": "Test message sent"}

