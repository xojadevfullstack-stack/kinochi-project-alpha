"""API v1 — Users endpoints."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.api.deps import get_user_service, get_current_admin
from app.application.users.service import UserService

router = APIRouter(prefix="/users", tags=["users"])

class UserCreateOrUpdate(BaseModel):
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None

class UserResponse(BaseModel):
    id: int
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    is_admin: bool
    is_banned: bool
    joined_at: datetime
    last_active_at: datetime

    model_config = {"from_attributes": True}

class PaginatedUsersResponse(BaseModel):
    items: list[UserResponse]
    total: int

@router.post("/register", response_model=UserResponse)
async def register_or_update(
    user_in: UserCreateOrUpdate,
    service: UserService = Depends(get_user_service)
):
    """Register or update a user (Called by bot)."""
    return await service.register_or_update(**user_in.model_dump())

@router.get("", response_model=PaginatedUsersResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    service: UserService = Depends(get_user_service),
    admin: dict = Depends(get_current_admin)
):
    """List all users (Admin only)."""
    users, total = await service.list_users(skip=skip, limit=limit)
    return {"items": users, "total": total}

@router.get("/{telegram_id}", response_model=UserResponse)
async def get_user(
    telegram_id: int,
    service: UserService = Depends(get_user_service),
    admin: dict = Depends(get_current_admin)
):
    """Get user by telegram ID (Admin only)."""
    user = await service.get_by_telegram_id(telegram_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/{telegram_id}/ban", status_code=status.HTTP_204_NO_CONTENT)
async def ban_user(
    telegram_id: int,
    service: UserService = Depends(get_user_service),
    admin: dict = Depends(get_current_admin)
):
    """Ban a user (Admin only)."""
    success = await service.ban(telegram_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")

@router.post("/{telegram_id}/unban", status_code=status.HTTP_204_NO_CONTENT)
async def unban_user(
    telegram_id: int,
    service: UserService = Depends(get_user_service),
    admin: dict = Depends(get_current_admin)
):
    """Unban a user (Admin only)."""
    success = await service.unban(telegram_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
