"""
Shared API dependencies — auth, pagination, DB session injection.

Presentation Layer: dependency functions injected into FastAPI route
handlers via Depends().
"""
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.repositories.movie_repo import MovieRepositoryImpl
from app.infrastructure.db.repositories.category_repo import CategoryRepositoryImpl
from app.infrastructure.db.repositories.user_repo import UserRepositoryImpl
from app.infrastructure.db.repositories.channel_repo import MandatoryChannelRepositoryImpl
from app.infrastructure.db.repositories.broadcast_repo import BroadcastRepositoryImpl
from app.application.movies.service import MovieService
from app.application.categories.service import CategoryService
from app.application.users.service import UserService
from app.application.channels.service import ChannelService
from app.application.broadcasts.service import BroadcastService
from app.infrastructure.db.models.admin_user import AdminUserModel
from app.infrastructure.security.jwt_handler import decode_token


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to provide a DB session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_movie_service(session: AsyncSession = Depends(get_db_session)) -> MovieService:
    """Dependency to provide MovieService."""
    repo = MovieRepositoryImpl(session)
    return MovieService(repo)


def get_category_service(session: AsyncSession = Depends(get_db_session)) -> CategoryService:
    """Dependency to provide CategoryService."""
    repo = CategoryRepositoryImpl(session)
    return CategoryService(repo)


def get_user_service(session: AsyncSession = Depends(get_db_session)) -> UserService:
    repo = UserRepositoryImpl(session)
    return UserService(repo)


def get_channel_service(session: AsyncSession = Depends(get_db_session)) -> ChannelService:
    repo = MandatoryChannelRepositoryImpl(session)
    return ChannelService(repo)


def get_broadcast_service(session: AsyncSession = Depends(get_db_session)) -> BroadcastService:
    b_repo = BroadcastRepositoryImpl(session)
    u_repo = UserRepositoryImpl(session)
    return BroadcastService(b_repo, u_repo)


async def get_current_admin(request: Request, session: AsyncSession = Depends(get_db_session)):
    """
    Dependency: validate access_token from httpOnly cookie.
    Returns admin dict. Raises 401 if token missing/invalid.
    """
    access_token = request.cookies.get("access_token")
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Autentifikatsiya talab qilinadi",
        )

    payload = decode_token(access_token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token yaroqsiz yoki muddati tugagan",
        )

    admin_id = payload.get("sub")
    result = await session.execute(
        select(AdminUserModel).where(AdminUserModel.id == int(admin_id))
    )
    admin = result.scalar_one_or_none()
    if not admin or not admin.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin topilmadi yoki nofaol",
        )

    return {"admin_id": admin.id, "email": admin.email, "role": admin.role}

