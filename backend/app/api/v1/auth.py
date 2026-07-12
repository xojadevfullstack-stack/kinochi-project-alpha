"""API v1 — Auth endpoints (login, logout, refresh, me).

Xavfsizlik qoidalari:
  - Login xato holatlarini FARQLAMAYMIZ: har doim generic
    "Email yoki parol noto'g'ri" xabari qaytariladi (user enumeration himoyasi).
  - Parol hech qachon log'ga yozilmaydi, response'da qaytarilmaydi.
  - Tokenlar httpOnly cookie sifatida o'rnatiladi (XSS himoyasi).
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db_session
from app.infrastructure.db.models.admin_user import AdminUserModel
from app.infrastructure.security.password_hasher import verify_password
from app.infrastructure.security.jwt_handler import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])

# Cookie settings
_COOKIE_DOMAIN = None  # None = same domain
_COOKIE_SECURE = settings.APP_ENV != "development"  # HTTPS only in prod
_COOKIE_SAMESITE = "lax"  # lax for dev (cross-port), strict for prod
_COOKIE_PATH = "/"


# ── Schemas ──────────────────────────────────────────────────────
class LoginRequest(BaseModel):
    email: str
    password: str


class AdminMeResponse(BaseModel):
    id: int
    email: str
    role: str
    is_active: bool

    model_config = {"from_attributes": True}


# ── Helper ───────────────────────────────────────────────────────
def _set_auth_cookies(response: Response, access_token: str, refresh_token: str) -> None:
    """Set httpOnly cookies for both tokens."""
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        path=_COOKIE_PATH,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite=_COOKIE_SAMESITE,
        path=_COOKIE_PATH,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
    )


def _clear_auth_cookies(response: Response) -> None:
    """Clear auth cookies by setting max_age=0."""
    response.delete_cookie(key="access_token", path=_COOKIE_PATH)
    response.delete_cookie(key="refresh_token", path=_COOKIE_PATH)


# ── Endpoints ────────────────────────────────────────────────────
@router.post("/login")
async def login(
    login_in: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
):
    """Authenticate admin and set httpOnly cookies."""
    # Find admin by email
    result = await session.execute(
        select(AdminUserModel).where(AdminUserModel.email == login_in.email)
    )
    admin = result.scalar_one_or_none()

    # Generic error — don't reveal whether email exists
    if not admin or not verify_password(login_in.password, admin.hashed_password):
        logger.warning("Login urinishi muvaffaqiyatsiz: %s", login_in.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email yoki parol noto'g'ri",
        )

    if not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akkaunt nofaol",
        )

    # Create tokens
    subject = str(admin.id)
    access_token = create_access_token(subject, extra={"email": admin.email, "role": admin.role})
    refresh_token = create_refresh_token(subject)

    _set_auth_cookies(response, access_token, refresh_token)

    return {
        "message": "Tizimga kirildi",
        "admin": AdminMeResponse.model_validate(admin).model_dump(),
    }


@router.post("/logout")
async def logout(response: Response):
    """Clear auth cookies."""
    _clear_auth_cookies(response)
    return {"message": "Tizimdan chiqildi"}


@router.post("/refresh")
async def refresh(
    request: Request,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
):
    """Use refresh_token cookie to issue new access_token."""
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token topilmadi")

    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Refresh token yaroqsiz yoki muddati tugagan")

    admin_id = payload.get("sub")
    result = await session.execute(
        select(AdminUserModel).where(AdminUserModel.id == int(admin_id))
    )
    admin = result.scalar_one_or_none()
    if not admin or not admin.is_active:
        _clear_auth_cookies(response)
        raise HTTPException(status_code=401, detail="Admin topilmadi yoki nofaol")

    # Issue fresh tokens
    new_access = create_access_token(str(admin.id), extra={"email": admin.email, "role": admin.role})
    new_refresh = create_refresh_token(str(admin.id))
    _set_auth_cookies(response, new_access, new_refresh)

    return {"message": "Token yangilandi"}


@router.get("/me", response_model=AdminMeResponse)
async def me(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Return current admin info from access_token cookie."""
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(status_code=401, detail="Autentifikatsiya talab qilinadi")

    payload = decode_token(access_token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Token yaroqsiz yoki muddati tugagan")

    admin_id = payload.get("sub")
    result = await session.execute(
        select(AdminUserModel).where(AdminUserModel.id == int(admin_id))
    )
    admin = result.scalar_one_or_none()
    if not admin or not admin.is_active:
        raise HTTPException(status_code=401, detail="Admin topilmadi yoki nofaol")

    return admin
