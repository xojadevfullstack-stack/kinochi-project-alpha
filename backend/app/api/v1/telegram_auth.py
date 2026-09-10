"""API v1 — Telegram Auth endpoints (Widget & WebApp)."""
import hmac
import hashlib
import time
import logging
from urllib.parse import parse_qsl
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db_session
from app.infrastructure.db.models.user import UserModel
from app.infrastructure.security.jwt_handler import create_access_token
from app.core.config import settings
from app.api.limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["telegram-auth"])

# ── Schemas ──────────────────────────────────────────────────────
class TelegramWidgetAuthRequest(BaseModel):
    id: int
    first_name: str | None = None
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str

class TelegramWebAppAuthRequest(BaseModel):
    initData: str


# ── Helpers ──────────────────────────────────────────────────────
def _set_user_cookie(response: Response, access_token: str) -> None:
    # Set httpOnly cookie for the user JWT
    secure = settings.APP_ENV != "development"
    response.set_cookie(
        key="user_access_token",
        value=access_token,
        httponly=True,
        secure=secure,
        samesite="lax",
        path="/",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )

async def _upsert_telegram_user(
    session: AsyncSession, 
    telegram_id: int, 
    first_name: str | None, 
    last_name: str | None, 
    username: str | None
) -> UserModel:
    """Finds or creates a user based on telegram_id."""
    result = await session.execute(select(UserModel).where(UserModel.telegram_id == telegram_id))
    user = result.scalar_one_or_none()

    if user:
        # Update details if needed
        user.first_name = first_name or user.first_name
        user.last_name = last_name or user.last_name
        user.username = username or user.username
    else:
        user = UserModel(
            telegram_id=telegram_id,
            first_name=first_name,
            last_name=last_name,
            username=username
        )
        session.add(user)

    await session.commit()
    await session.refresh(user)
    return user


# ── Endpoints ────────────────────────────────────────────────────
@router.post("/telegram-login")
@limiter.limit("5/minute")
async def telegram_login_widget(
    data: TelegramWidgetAuthRequest,
    response: Response,
    request: Request,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Authenticate using Telegram Login Widget.
    Secret key = SHA256(bot_token).
    Uses hmac.compare_digest for constant-time comparison.
    """
    # 1. Replay protection (86400 seconds = 24 hours)
    current_time = int(time.time())
    if current_time - data.auth_date > 86400:
        raise HTTPException(status_code=401, detail="Auth date is expired.")

    # 2. Build data_check_string
    data_dict = data.model_dump(exclude={"hash"}, exclude_none=True)
    # Sort alphabetically by key
    sorted_items = sorted(data_dict.items(), key=lambda x: x[0])
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted_items])

    # 3. Compute hash
    bot_token = settings.BOT_TOKEN
    if not bot_token:
        raise HTTPException(status_code=500, detail="BOT_TOKEN not configured.")
        
    secret_key = hashlib.sha256(bot_token.encode('utf-8')).digest()
    computed_hash = hmac.new(
        secret_key, 
        data_check_string.encode('utf-8'), 
        hashlib.sha256
    ).hexdigest()

    # 4. Compare hash securely
    if not hmac.compare_digest(computed_hash, data.hash):
        raise HTTPException(status_code=401, detail="Invalid hash.")

    # 5. Upsert user
    user = await _upsert_telegram_user(
        session=session,
        telegram_id=data.id,
        first_name=data.first_name,
        last_name=data.last_name,
        username=data.username
    )

    if user.is_banned:
        raise HTTPException(status_code=403, detail="User is banned.")

    # 6. Issue JWT
    access_token = create_access_token(
        subject=str(user.id), 
        extra={"telegram_id": user.telegram_id, "role": "user"}
    )
    _set_user_cookie(response, access_token)

    return {"message": "Login successful", "access_token": access_token}


@router.post("/telegram-webapp")
@limiter.limit("5/minute")
async def telegram_webapp_initdata(
    data: TelegramWebAppAuthRequest,
    response: Response,
    request: Request,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Authenticate using Telegram WebApp initData.
    Secret key = HMAC_SHA256(key="WebAppData", data=bot_token).
    Uses hmac.compare_digest for constant-time comparison.
    """
    init_data = data.initData
    
    # 1. Parse query string
    parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
    
    if "hash" not in parsed_data:
        raise HTTPException(status_code=401, detail="Hash missing from initData.")
        
    received_hash = parsed_data.pop("hash")
    
    # 2. Check auth_date (Replay protection)
    auth_date_str = parsed_data.get("auth_date")
    if not auth_date_str or not auth_date_str.isdigit():
        raise HTTPException(status_code=401, detail="Invalid auth_date.")
        
    current_time = int(time.time())
    if current_time - int(auth_date_str) > 86400:
        raise HTTPException(status_code=401, detail="Auth date is expired.")

    # 3. Build data_check_string
    sorted_items = sorted(parsed_data.items(), key=lambda x: x[0])
    data_check_string = "\n".join([f"{k}={v}" for k, v in sorted_items])

    # 4. Compute hash
    bot_token = settings.BOT_TOKEN
    if not bot_token:
        raise HTTPException(status_code=500, detail="BOT_TOKEN not configured.")
        
    secret_key = hmac.new(
        "WebAppData".encode('utf-8'),
        bot_token.encode('utf-8'),
        hashlib.sha256
    ).digest()
    
    computed_hash = hmac.new(
        secret_key,
        data_check_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()

    # 5. Compare hash securely
    if not hmac.compare_digest(computed_hash, received_hash):
        raise HTTPException(status_code=401, detail="Invalid hash.")

    # 6. Extract user info and Upsert
    import json
    user_str = parsed_data.get("user")
    if not user_str:
        raise HTTPException(status_code=401, detail="User data missing from initData.")
        
    try:
        user_info = json.loads(user_str)
    except json.JSONDecodeError:
        raise HTTPException(status_code=401, detail="Invalid user JSON.")
        
    telegram_id = user_info.get("id")
    if not telegram_id:
        raise HTTPException(status_code=401, detail="User ID missing.")
        
    user = await _upsert_telegram_user(
        session=session,
        telegram_id=telegram_id,
        first_name=user_info.get("first_name"),
        last_name=user_info.get("last_name"),
        username=user_info.get("username")
    )
    
    if user.is_banned:
        raise HTTPException(status_code=403, detail="User is banned.")

    # 7. Issue JWT
    access_token = create_access_token(
        subject=str(user.id), 
        extra={"telegram_id": user.telegram_id, "role": "user"}
    )
    _set_user_cookie(response, access_token)

    return {"message": "Login successful", "access_token": access_token}
