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


def test_smm_settings_admin_telegram_id_and_progress_endpoint(admin_client):
    u = admin_client.put("/api/v1/smm/settings", json={"admin_telegram_id": "123456789"})
    assert u.status_code == 200
    assert u.json()["admin_telegram_id"] == "123456789"

    gen = admin_client.post(
        "/api/v1/smm/jobs",
        json={"media_type": "movie", "movie_code": "3957", "title": "Progress Test", "generate": True},
    )
    assert gen.status_code == 201
    assert gen.json()["status"] == "generating"
    assert gen.json()["progress_pct"] == 0

    prog = admin_client.get("/api/v1/smm/progress")
    assert prog.status_code == 200
    pdata = prog.json()
    assert "cycle1" in pdata and "cycle2" in pdata
    assert pdata["cycle2"]["generating"] >= 1
    assert any(j["title"] == "Progress Test" for j in pdata["cycle2"]["active_jobs"])
    assert "worker" in pdata and "enabled" in pdata["worker"]


def test_smm_bot_secret_allows_approve_and_reject_from_telegram(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "BOT_API_SECRET", "bot_secret_xyz")
    app.dependency_overrides[get_current_admin] = lambda: {"id": 1, "username": "xojadevops", "role": "superadmin"}
    try:
        c = client.post(
            "/api/v1/smm/jobs",
            json={"media_type": "movie", "movie_code": "3958", "title": "Bot Inline Test"},
        )
        jid = c.json()["id"]
    finally:
        app.dependency_overrides.pop(get_current_admin, None)

    # Unauthenticated without bot secret must be rejected
    no_auth = client.post(f"/api/v1/smm/bot/jobs/{jid}/approve", json={"publish_now": True})
    assert no_auth.status_code in (401, 403)

    # Valid X-Bot-Secret approves -> publishing
    ok_pub = client.post(
        f"/api/v1/smm/bot/jobs/{jid}/approve",
        json={"publish_now": True},
        headers={"X-Bot-Secret": "bot_secret_xyz"},
    )
    assert ok_pub.status_code == 200
    assert ok_pub.json()["status"] == "publishing"

    # Valid X-Bot-Secret rejects
    ok_rej = client.post(
        f"/api/v1/smm/bot/jobs/{jid}/reject",
        headers={"X-Bot-Secret": "bot_secret_xyz"},
    )
    assert ok_rej.status_code == 200
    assert ok_rej.json()["status"] == "rejected"


def test_smm_job_video_endpoint_serves_file_and_404_when_missing(admin_client, tmp_path):
    mp4 = tmp_path / "clip_sample.mp4"
    mp4.write_bytes(b"\x00\x00\x00\x18ftypmp42")
    created = admin_client.post(
        "/api/v1/smm/jobs",
        json={"media_type": "movie", "movie_code": "3960", "title": "Video Stream Test", "clip_path": str(mp4)},
    )
    assert created.status_code == 201
    jid = created.json()["id"]

    ok = admin_client.get(f"/api/v1/smm/jobs/{jid}/video")
    assert ok.status_code == 200
    assert ok.headers["content-type"].startswith("video/mp4")

    missing = admin_client.post(
        "/api/v1/smm/jobs",
        json={"media_type": "movie", "movie_code": "3961", "title": "Missing Video", "clip_path": str(tmp_path / "missing.mp4")},
    )
    miss_resp = admin_client.get(f"/api/v1/smm/jobs/{missing.json()['id']}/video")
    assert miss_resp.status_code == 404


def test_smm_bot_endpoint_authorizes_db_admin_telegram_id_when_env_empty(client, monkeypatch):
    from app.core.config import settings

    monkeypatch.setattr(settings, "BOT_API_SECRET", "bot_secret_db_auth")
    monkeypatch.delenv("ADMIN_IDS", raising=False)
    monkeypatch.delenv("SMM_ADMIN_TELEGRAM_ID", raising=False)

    app.dependency_overrides[get_current_admin] = lambda: {"id": 1, "username": "xojadevops", "role": "superadmin"}
    try:
        client.put("/api/v1/smm/settings", json={"admin_telegram_id": "1990156236"})
        c = client.post("/api/v1/smm/jobs", json={"media_type": "movie", "movie_code": "3965", "title": "DB Admin Auth"})
        jid = c.json()["id"]
    finally:
        app.dependency_overrides.pop(get_current_admin, None)

    r_bad = client.post(
        f"/api/v1/smm/bot/jobs/{jid}/approve",
        json={"publish_now": True, "telegram_user_id": 111111},
        headers={"X-Bot-Secret": "bot_secret_db_auth"},
    )
    assert r_bad.status_code == 403

    r_ok = client.post(
        f"/api/v1/smm/bot/jobs/{jid}/approve",
        json={"publish_now": True, "telegram_user_id": 1990156236},
        headers={"X-Bot-Secret": "bot_secret_db_auth"},
    )
    assert r_ok.status_code == 200
    assert r_ok.json()["status"] == "publishing"


def test_get_worker_state_safe_never_swallows_import_error_and_ensures_repo_path(monkeypatch):
    import sys
    from app.api.v1 import smm as smm_api

    monkeypatch.setitem(sys.modules, "scraper.smm_worker", None)
    state = smm_api._get_worker_state_safe()
    assert state["running"] is False
    assert state["last_error"] is not None
    assert "ModuleNotFoundError" in state["last_error"]
