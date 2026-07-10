"""JWT access & refresh token creation and verification via PyJWT.

Trade-off qaror (MVP):
  Refresh token DB'da SAQLANMAYDI — stateless JWT yondashuvi tanlanadi.
  Sabab: MVP uchun oddiylik muhimroq. Revocation/logout-everywhere
  imkoniyati yo'q, lekin token muddati qisqa (access: 30 min,
  refresh: 7 kun) bo'lgani uchun xavf past. Kelajakda DB-backed
  refresh token qo'shish mumkin (alohida jadval + cleanup cron).
"""
from datetime import datetime, timedelta, timezone

import jwt

from app.core.config import settings


_ALGORITHM = "HS256"


def create_access_token(subject: str, extra: dict | None = None) -> str:
    """Create a short-lived access token (default 30 min)."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire, "type": "access"}
    if extra:
        payload.update(extra)
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """Create a long-lived refresh token (default 7 days)."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {"sub": subject, "exp": expire, "type": "refresh"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)


def decode_token(token: str) -> dict | None:
    """Decode and verify a JWT. Returns payload dict or None on failure."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None
