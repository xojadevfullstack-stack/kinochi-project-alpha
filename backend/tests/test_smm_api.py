import pytest
from app.api.deps import get_current_admin
from app.main import app


@pytest.fixture
def admin_client(client):
    app.dependency_overrides[get_current_admin] = lambda: {"id": 1, "username": "xojadevops", "role": "superadmin"}
    yield client
    app.dependency_overrides.pop(get_current_admin, None)


def test_smm_endpoints_require_admin_auth(client):
    r = client.get("/api/v1/smm/settings")
    assert r.status_code in (401, 403)


def test_smm_settings_get_and_toggle_dual_mode(admin_client):
    r = admin_client.get("/api/v1/smm/settings")
    assert r.status_code == 200
    data = r.json()
    assert data["mode"] == "SEMI_AUTO"
    assert "telegram" in data["enabled_platforms"]

    u = admin_client.put(
        "/api/v1/smm/settings",
        json={"mode": "FULL_AUTO", "daily_limit": 4, "copyright_shield": True},
    )
    assert u.status_code == 200
    updated = u.json()
    assert updated["mode"] == "FULL_AUTO"
    assert updated["daily_limit"] == 4
    assert updated["copyright_shield"] is True


def test_smm_jobs_lifecycle_approve_recut_and_reject(admin_client):
    # Ensure SEMI_AUTO mode first
    admin_client.put("/api/v1/smm/settings", json={"mode": "SEMI_AUTO"})

    c = admin_client.post(
        "/api/v1/smm/jobs",
        json={"media_type": "movie", "media_id": 10, "movie_code": "889", "title": "Otamga qasida", "start_sec": 420.0, "duration_sec": 45.0},
    )
    assert c.status_code == 201
    job = c.json()
    assert job["status"] == "waiting_approval"
    job_id = job["id"]

    # Recut updates timestamps and marks generating
    rc = admin_client.post(f"/api/v1/smm/jobs/{job_id}/recut", json={"start_sec": 600.0, "duration_sec": 35.0})
    assert rc.status_code == 200
    assert rc.json()["start_sec"] == 600.0
    assert rc.json()["status"] == "generating"

    # Approve -> scheduled or publishing
    ap = admin_client.post(f"/api/v1/smm/jobs/{job_id}/approve", json={"publish_now": True})
    assert ap.status_code == 200
    assert ap.json()["status"] == "publishing"

    # Reject another job
    c2 = admin_client.post("/api/v1/smm/jobs", json={"media_type": "movie", "movie_code": "901", "title": "Test 2"})
    rj = admin_client.post(f"/api/v1/smm/jobs/{c2.json()['id']}/reject")
    assert rj.status_code == 200
    assert rj.json()["status"] == "rejected"

    lst = admin_client.get("/api/v1/smm/jobs")
    assert lst.status_code == 200
    assert len(lst.json()) >= 2
