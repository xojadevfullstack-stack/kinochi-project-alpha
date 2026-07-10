"""
Superadmin yaratish skripti — bir martalik CLI.

Ishga tushirish (Docker konteyner ichida):
  docker-compose exec backend python -m scripts.create_superadmin

Yoki to'g'ridan-to'g'ri:
  python -m scripts.create_superadmin

MUHIM: Hech qanday ochiq /register endpoint yaratilmagan.
Bu yagona admin yaratish usuli.
"""
import asyncio
import getpass
import sys
import os

# app modulini topishi uchun project root'ni sys.path'ga qo'shamiz
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.admin_user import AdminUserModel
from app.infrastructure.security.password_hasher import hash_password


async def main():
    print("=" * 50)
    print("  Kinochi — Superadmin yaratish")
    print("=" * 50)
    print()

    email = input("Email: ").strip()
    if not email or "@" not in email:
        print("❌ Noto'g'ri email format.")
        return

    password = getpass.getpass("Parol: ")
    if len(password) < 6:
        print("❌ Parol kamida 6 ta belgi bo'lishi kerak.")
        return

    password_confirm = getpass.getpass("Parolni tasdiqlang: ")
    if password != password_confirm:
        print("❌ Parollar mos kelmaydi.")
        return

    async with async_session_factory() as session:
        # Check if email already exists
        result = await session.execute(
            select(AdminUserModel).where(AdminUserModel.email == email)
        )
        existing = result.scalar_one_or_none()
        if existing:
            print(f"❌ Bu email allaqachon mavjud (ID: {existing.id}).")
            return

        admin = AdminUserModel(
            email=email,
            hashed_password=hash_password(password),
            is_active=True,
            role="superadmin",
        )
        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        print()
        print(f"✅ Superadmin yaratildi!")
        print(f"   ID:    {admin.id}")
        print(f"   Email: {admin.email}")
        print(f"   Role:  {admin.role}")


if __name__ == "__main__":
    asyncio.run(main())
