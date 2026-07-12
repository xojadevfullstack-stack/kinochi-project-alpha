import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.infrastructure.db.models.admin_user import AdminUserModel
from unittest.mock import patch, AsyncMock
from app.infrastructure.security.jwt_handler import create_access_token

@pytest.fixture
def mock_db_session():
    return AsyncMock()

@pytest.mark.asyncio
async def test_login_success():
    # Setup
    admin_mock = AdminUserModel(
        id=1,
        email="admin@test.com",
        role="superadmin",
        is_active=True,
        hashed_password="mocked_hashed_password"
    )
    
    with patch("app.api.v1.auth.get_db_session") as mock_get_db, \
         patch("app.api.v1.auth.verify_password", return_value=True):
        # Mock session dependency
        mock_session = AsyncMock()
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = admin_mock
        mock_session.execute.return_value = mock_result
        
        async def override_get_db():
            yield mock_session
            
        from app.api.deps import get_db_session
        app.dependency_overrides[get_db_session] = override_get_db
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/api/v1/auth/login", json={
                "email": "admin@test.com",
                "password": "correct_password"
            })
            
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Tizimga kirildi"
        assert data["admin"]["email"] == "admin@test.com"
        assert "access_token" not in data # Ensure access_token is stripped from body
        
        # Check cookie
        assert "access_token" in response.cookies
        
        # Cleanup
        app.dependency_overrides.pop(get_db_session, None)


@pytest.mark.asyncio
async def test_login_wrong_password():
    # Setup
    admin_mock = AdminUserModel(
        id=1,
        email="admin@test.com",
        role="superadmin",
        is_active=True,
        hashed_password="mocked_hashed_password"
    )
    
    with patch("app.api.v1.auth.get_db_session") as mock_get_db, \
         patch("app.api.v1.auth.verify_password", return_value=False):
        mock_session = AsyncMock()
        from unittest.mock import MagicMock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = admin_mock
        mock_session.execute.return_value = mock_result
        
        async def override_get_db():
            yield mock_session
            
        from app.api.deps import get_db_session
        app.dependency_overrides[get_db_session] = override_get_db
        
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            response = await ac.post("/api/v1/auth/login", json={
                "email": "admin@test.com",
                "password": "wrong_password"
            })
            
        assert response.status_code == 401
        data = response.json()
        assert data["detail"] == "Email yoki parol noto'g'ri"
        
        # Cleanup
        app.dependency_overrides.pop(get_db_session, None)
