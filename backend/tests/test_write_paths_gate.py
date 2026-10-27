"""
Tests for Write Paths through Admission Gate (B3).
Ensures API endpoints and ingestion paths enforce the gate and reject invalid data.
"""
import subprocess
import sys
import os
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_admin, get_db_session


def test_scripts_enforce_bypass_flag():
    """clean_dirty_db_records.py va fix_anime_everything_db.py bypass flagsiz to'xtashini tekshirish."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    env = {**os.environ, "PYTHONPATH": f"{repo_root}{os.pathsep}{os.environ.get('PYTHONPATH', '')}"}
    res1 = subprocess.run(
        [sys.executable, os.path.join(repo_root, "scripts", "clean_dirty_db_records.py")],
        capture_output=True,
        text=True,
        cwd=repo_root,
        env=env
    )
    assert res1.returncode == 1
    assert "Admission Gate" in res1.stdout

    res2 = subprocess.run(
        [sys.executable, os.path.join(repo_root, "scripts", "fix_anime_everything_db.py")],
        capture_output=True,
        text=True,
        cwd=repo_root,
        env=env
    )
    assert res2.returncode == 1
    assert "Admission Gate" in res2.stdout


def test_create_movie_gate_validation():
    """POST /api/v1/movies gate pre_check tekshiruvini bajarishini tekshirish."""
    client = TestClient(app)

    async def mock_admin():
        return {"id": 1, "username": "admin", "role": "admin"}

    mock_db = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    app.dependency_overrides[get_current_admin] = mock_admin
    app.dependency_overrides[get_db_session] = lambda: mock_db

    try:
        # Invalid payload: short title and invalid year
        response = client.post(
            "/api/v1/movies",
            json={
                "title": "A",
                "release_year": 1800,
                "description": "Short",
                "manual_verified": False
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "defects" in data["detail"]
    finally:
        app.dependency_overrides.clear()


def test_create_series_gate_validation():
    """POST /api/v1/series gate pre_check tekshiruvini bajarishini tekshirish."""
    client = TestClient(app)

    async def mock_admin():
        return {"id": 1, "username": "admin", "role": "admin"}

    mock_db = AsyncMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    app.dependency_overrides[get_current_admin] = mock_admin
    app.dependency_overrides[get_db_session] = lambda: mock_db

    try:
        response = client.post(
            "/api/v1/series",
            json={
                "title": "A",
                "release_year": 1700,
                "description": "Short",
                "manual_verified": False
            }
        )
        assert response.status_code == 400
        data = response.json()
        assert "defects" in data["detail"]
    finally:
        app.dependency_overrides.clear()
