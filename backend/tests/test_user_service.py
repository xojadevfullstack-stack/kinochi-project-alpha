import pytest
from app.domain.users.entities import User
from app.application.users.service import UserService

class FakeUserRepository:
    def __init__(self):
        self.users = {}
        self.counter = 1

    async def create_or_update(self, user: User) -> User:
        if user.telegram_id in self.users:
            existing = self.users[user.telegram_id]
            if user.username is not None: existing.username = user.username
            if user.first_name is not None: existing.first_name = user.first_name
            if user.last_name is not None: existing.last_name = user.last_name
            return existing
        else:
            user.id = self.counter
            self.counter += 1
            self.users[user.telegram_id] = user
            return user

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        return self.users.get(telegram_id)

    async def list_users(self, skip: int = 0, limit: int = 20) -> tuple[list[User], int]:
        users = list(self.users.values())[skip:skip+limit]
        return users, len(self.users)

    async def set_ban_status(self, telegram_id: int, is_banned: bool) -> bool:
        if telegram_id in self.users:
            self.users[telegram_id].is_banned = is_banned
            return True
        return False

@pytest.fixture
def user_service():
    repo = FakeUserRepository()
    return UserService(repo)

@pytest.mark.asyncio
async def test_register_or_update(user_service: UserService):
    user = await user_service.register_or_update(
        telegram_id=123, username="testuser", first_name="Test"
    )
    assert user.id is not None
    assert user.telegram_id == 123
    assert user.username == "testuser"
    assert user.first_name == "Test"

    # Update
    updated = await user_service.register_or_update(
        telegram_id=123, first_name="Updated"
    )
    assert updated.id == user.id
    assert updated.first_name == "Updated"

@pytest.mark.asyncio
async def test_get_user(user_service: UserService):
    await user_service.register_or_update(telegram_id=123, username="test")
    user = await user_service.get_by_telegram_id(123)
    assert user is not None
    assert user.telegram_id == 123

@pytest.mark.asyncio
async def test_ban_unban(user_service: UserService):
    await user_service.register_or_update(telegram_id=123)
    assert await user_service.ban(123) is True
    user = await user_service.get_by_telegram_id(123)
    assert user.is_banned is True

    assert await user_service.unban(123) is True
    user = await user_service.get_by_telegram_id(123)
    assert user.is_banned is False

@pytest.mark.asyncio
async def test_list_users(user_service: UserService):
    await user_service.register_or_update(telegram_id=1)
    await user_service.register_or_update(telegram_id=2)
    users, total = await user_service.list_users()
    assert total == 2
    assert len(users) == 2
