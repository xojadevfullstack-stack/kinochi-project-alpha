import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.admin_user import AdminUserModel
from app.infrastructure.security.password_hasher import hash_password

async def main():
    async with async_session_factory() as session:
        admin = AdminUserModel(
            email="admin@kinochi.uz",
            hashed_password=hash_password("admin123"),
            is_active=True,
            role="superadmin",
        )
        session.add(admin)
        await session.commit()
        print("Superadmin created: admin@kinochi.uz / admin123")

if __name__ == "__main__":
    asyncio.run(main())
