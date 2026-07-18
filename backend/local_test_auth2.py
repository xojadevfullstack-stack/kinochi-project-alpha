import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.infrastructure.security.jwt_handler import create_access_token
from app.infrastructure.db.session import async_session_factory
from app.infrastructure.db.models.admin_user import AdminUserModel
from sqlalchemy import select

async def setup_admin():
    async with async_session_factory() as session:
        result = await session.execute(select(AdminUserModel).where(AdminUserModel.email == "admin@kinochi.uz"))
        admin = result.scalar_one_or_none()
        if not admin:
            admin = AdminUserModel(email="admin@kinochi.uz", password_hash="dummy", role="superadmin", is_active=True)
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
        return admin.id

admin_id = asyncio.run(setup_admin())
token = create_access_token(str(admin_id), {"email": "admin@kinochi.uz", "role": "superadmin"})

client = TestClient(app)
response = client.post("/api/v1/movies", json={
    "title": "Test Movie",
    "category_ids": [],
    "page_ids": []
}, headers={"Authorization": f"Bearer {token}"})

print("STATUS:", response.status_code)
print("BODY:", response.text)
