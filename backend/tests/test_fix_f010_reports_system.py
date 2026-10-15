import pytest
from unittest.mock import AsyncMock, MagicMock
from starlette.requests import Request
from fastapi import HTTPException
from app.infrastructure.db.models.report import ReportModel
from app.infrastructure.db.models.movie import MovieModel
from app.api.v1.reports import create_report, update_report_status, ReportUpdateStatus, list_reports_grouped


def test_f010_report_model_has_telegram_user_id():
    """F-010 regression: ReportModel must have telegram_user_id column."""
    assert hasattr(ReportModel, "telegram_user_id"), "ReportModel must have telegram_user_id"
    col = ReportModel.__table__.columns.get("telegram_user_id")
    assert col is not None, "telegram_user_id column missing on reports table"


@pytest.mark.asyncio
async def test_f010_reports_dedup_per_user(monkeypatch):
    """F-010 regression: Per-user duplicate pending reports must be rejected with 400."""
    mock_db = AsyncMock()

    # Mock movie lookup: movie exists
    movie_mock = MovieModel(id=1, title="Test Movie", code="TEST01", publish_status="published")
    m_res = MagicMock()
    m_res.scalar_one_or_none.return_value = movie_mock

    # Mock dedup query: already exists an active pending report for this user
    dedup_res = MagicMock()
    dedup_res.scalar_one_or_none.return_value = 999  # existing report id

    # Return movie lookup first, then dedup lookup
    mock_db.execute.side_effect = [m_res, dedup_res]

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/reports",
        "headers": [],
        "client": ("127.0.0.1", 12345),
        "app": None,
    }
    req = Request(scope)

    with pytest.raises(HTTPException) as exc_info:
        await create_report(
            request=req,
            media_type="movie",
            issue_type="wrong_video",
            movie_id=1,
            telegram_user_id=12345678,
            db=mock_db
        )

    assert exc_info.value.status_code == 400
    assert "allaqachon" in exc_info.value.detail.lower()


@pytest.mark.asyncio
async def test_f010_reports_auto_hide_threshold(monkeypatch):
    """F-010 regression: Auto-hide media when pending reports threshold is reached."""
    # Mock telegram sending
    monkeypatch.setattr("app.api.v1.reports.telegram_client.send_message", AsyncMock(return_value=True))

    mock_db = AsyncMock()

    # Movie initially published
    movie_mock = MovieModel(id=1, title="Buggy Movie", code="BUG01", publish_status="published")
    m_res = MagicMock()
    m_res.scalar_one_or_none.return_value = movie_mock

    # Dedup check: no duplicate
    dedup_res = MagicMock()
    dedup_res.scalar_one_or_none.return_value = None

    # Count query: 4 pending reports already exist -> this 5th report triggers threshold
    count_res = MagicMock()
    count_res.scalar.return_value = 4

    # Movie lookup for auto-hide update
    m_update_res = MagicMock()
    m_update_res.scalar_one_or_none.return_value = movie_mock

    mock_db.execute.side_effect = [m_res, dedup_res, count_res, m_update_res]

    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/reports",
        "headers": [],
        "client": ("127.0.0.2", 12345),
        "app": None,
    }
    req = Request(scope)

    resp = await create_report(
        request=req,
        media_type="movie",
        issue_type="broken_trailer",
        movie_id=1,
        telegram_user_id=98765432,
        db=mock_db
    )

    assert resp["status"] == "success"
    # The movie must be hidden automatically due to reaching 5 reports
    assert movie_mock.publish_status == "hidden"


@pytest.mark.asyncio
async def test_f010_restore_media_on_resolve():
    """F-010 regression: update_report_status with restore_media=True restores hidden media."""
    mock_db = AsyncMock()

    # The report being resolved
    report_mock = ReportModel(
        id=55,
        media_type="movie",
        movie_id=10,
        status="pending"
    )
    r_res = MagicMock()
    r_res.scalar_one_or_none.return_value = report_mock

    # Remaining pending reports for this movie: 0
    rem_res = MagicMock()
    rem_res.scalar.return_value = 0

    # Movie currently hidden
    movie_mock = MovieModel(id=10, title="Fixed Movie", code="FIX01", publish_status="hidden")
    m_res = MagicMock()
    m_res.scalar_one_or_none.return_value = movie_mock

    mock_db.execute.side_effect = [r_res, rem_res, m_res]

    data = ReportUpdateStatus(status="resolved", restore_media=True)
    res = await update_report_status(
        report_id=55,
        data=data,
        db=mock_db,
        admin={"sub": "admin"}
    )

    assert res["status"] == "ok"
    assert report_mock.status == "resolved"
    assert movie_mock.publish_status == "published"


@pytest.mark.asyncio
async def test_f010_list_reports_grouped():
    """F-010 regression: list_reports_grouped groups pending reports by media."""
    mock_db = AsyncMock()

    # Mock grouped query result
    group_rows = [
        ("movie", 10, None, 5, None),
    ]
    exec_res = MagicMock()
    exec_res.all.return_value = group_rows

    # Mock movie title lookup
    m_res = MagicMock()
    m_res.first.return_value = ("Test Movie", "TST01")

    mock_db.execute.side_effect = [exec_res, m_res]

    res = await list_reports_grouped(db=mock_db, admin={"sub": "admin"})

    assert "groups" in res
    assert len(res["groups"]) == 1
    assert res["groups"][0]["movie_id"] == 10
    assert res["groups"][0]["report_count"] == 5
    assert res["groups"][0]["media_title"] == "Test Movie"
