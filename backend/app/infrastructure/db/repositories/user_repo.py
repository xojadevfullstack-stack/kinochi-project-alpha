"""User repository implementation."""
from typing import Sequence
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.users.entities import User
from app.domain.users.repository import IUserRepository
from app.infrastructure.db.models.user import UserModel

class UserRepositoryImpl(IUserRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: UserModel) -> User:
        return User.model_validate(model)

    async def create_or_update(self, user: User) -> User:
        stmt = select(UserModel).where(UserModel.telegram_id == user.telegram_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        
        if model:
            if user.username is not None: model.username = user.username
            if user.first_name is not None: model.first_name = user.first_name
            if user.last_name is not None: model.last_name = user.last_name
        else:
            model = UserModel(
                telegram_id=user.telegram_id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                is_admin=user.is_admin,
                is_banned=user.is_banned
            )
            self.session.add(model)
            
        await self.session.commit()
        await self.session.refresh(model)
        return self._to_entity(model)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        stmt = select(UserModel).where(UserModel.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        model = result.scalar_one_or_none()
        return self._to_entity(model) if model else None

    async def list_users(self, skip: int = 0, limit: int = 20, is_banned: bool | None = None) -> tuple[Sequence[User], int]:
        stmt = select(UserModel)
        count_stmt = select(func.count(UserModel.id))
        
        if is_banned is not None:
            stmt = stmt.where(UserModel.is_banned == is_banned)
            count_stmt = count_stmt.where(UserModel.is_banned == is_banned)
            
        stmt = stmt.order_by(UserModel.id.desc()).offset(skip).limit(limit)
        
        result = await self.session.execute(stmt)
        models = result.scalars().all()
        
        total = await self.session.scalar(count_stmt) or 0
        
        return [self._to_entity(m) for m in models], total

    async def set_ban_status(self, telegram_id: int, is_banned: bool) -> bool:
        stmt = update(UserModel).where(UserModel.telegram_id == telegram_id).values(is_banned=is_banned)
        result = await self.session.execute(stmt)
        await self.session.commit()
        return result.rowcount > 0
