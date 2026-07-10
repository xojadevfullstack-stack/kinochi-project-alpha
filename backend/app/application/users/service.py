"""User application service."""
from typing import Sequence
from app.domain.users.entities import User
from app.domain.users.repository import IUserRepository

class UserService:
    def __init__(self, user_repo: IUserRepository):
        self.user_repo = user_repo

    async def register_or_update(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        return await self.user_repo.create_or_update(user)

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        return await self.user_repo.get_by_telegram_id(telegram_id)

    async def ban(self, telegram_id: int) -> bool:
        return await self.user_repo.set_ban_status(telegram_id, True)

    async def unban(self, telegram_id: int) -> bool:
        return await self.user_repo.set_ban_status(telegram_id, False)

    async def list_users(self, skip: int = 0, limit: int = 20) -> tuple[Sequence[User], int]:
        return await self.user_repo.list_users(skip=skip, limit=limit)
