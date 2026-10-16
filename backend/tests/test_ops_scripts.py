"""
backend/tests/test_ops_scripts.py: Ops skriptlarini tekshirish uchun to'liq unit va integratsion testlar.

Qamrov:
1. PowerShell skriptlari sintaksisi ([scriptblock]::Create).
2. ops/go_live.ps1 va ops/pilot.ps1 -DryRun tekshiruvlari (inertlik kafolati).
3. ops/db_checks.py: host sanitization, URL normalization, mock DB logic.
4. ops/redis_flush_cache.py: host sanitization, faqat cache:* kalitlari, tasdiqlash va batch o'chirish.
5. ops/new_telegram_session.py: xavfsiz faylga yozish, sir saqlash, force guard, mock avtorizatsiya.
"""

import os
import sys
import subprocess
import tempfile
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

# sys.path ga root qo'shish
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from ops.db_checks import get_sanitized_host, normalize_async_url, run_db_checks
from ops.redis_flush_cache import get_sanitized_redis_host, flush_cache_keys
from ops.new_telegram_session import save_session_to_env_file, create_telegram_session


# -------------------------------------------------------------
# 1. PowerShell skriptlari sintaksis testlari
# -------------------------------------------------------------
def test_powershell_go_live_syntax():
    """ops/go_live.ps1 sintaksisini [scriptblock]::Create orqali tekshirish."""
    script_path = os.path.join(ROOT_DIR, "ops", "go_live.ps1")
    assert os.path.exists(script_path), f"Fayl topilmadi: {script_path}"

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    cmd = ["powershell", "-NoProfile", "-Command", "[scriptblock]::Create($input) | Out-Null"]
    proc = subprocess.run(cmd, input=content, text=True, capture_output=True)
    assert proc.returncode == 0, f"go_live.ps1 sintaksisida xatolik: {proc.stderr}"


def test_go_live_halts_on_alembic_check_failure():
    """go_live.ps1 alembic check xato (diff) berganda exit 1 bilan to'xtashi shart (OF-002)."""
    script_path = os.path.join(ROOT_DIR, "ops", "go_live.ps1")
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "& alembic check" in content
    idx = content.find("& alembic check")
    sub = content[idx:idx+250]
    assert "exit 1" in sub, "alembic check xatolik berganda exit 1 chaqirilmagan!"


def test_go_live_verifies_backup_with_pg_restore():
    """go_live.ps1 zaxira olingandan so'ng pg_restore --list orqali yaxlitlikni tekshirishi shart (OF-003)."""
    script_path = os.path.join(ROOT_DIR, "ops", "go_live.ps1")
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "& pg_dump" in content
    idx = content.find("& pg_dump")
    sub = content[idx:idx+800]
    assert "pg_restore --list" in sub, "pg_restore --list chaqirilmagan!"




def test_powershell_pilot_syntax():
    """ops/pilot.ps1 sintaksisini [scriptblock]::Create orqali tekshirish."""
    script_path = os.path.join(ROOT_DIR, "ops", "pilot.ps1")
    assert os.path.exists(script_path), f"Fayl topilmadi: {script_path}"

    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    cmd = ["powershell", "-NoProfile", "-Command", "[scriptblock]::Create($input) | Out-Null"]
    proc = subprocess.run(cmd, input=content, text=True, capture_output=True)
    assert proc.returncode == 0, f"pilot.ps1 sintaksisida xatolik: {proc.stderr}"


# -------------------------------------------------------------
# 2. PowerShell -DryRun testlari (Inertlik)
# -------------------------------------------------------------
def test_go_live_dry_run_inert():
    """ops/go_live.ps1 -DryRun rejimida bazaga tegmasdan 0 bilan tugashi kerak."""
    script_path = os.path.join(ROOT_DIR, "ops", "go_live.ps1")
    env = os.environ.copy()
    env["OPS_TEST_DB_URL"] = "postgresql://dummyhost.internal:5432/testdb"

    cmd = [
        "powershell",
        "-NoProfile",
        "-File",
        script_path,
        "-DryRun",
        "-UrlEnvVar",
        "OPS_TEST_DB_URL",
    ]
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert proc.returncode == 0, f"go_live -DryRun muvaffaqiyatsiz bo'ldi:\n{proc.stdout}\n{proc.stderr}"
    assert "dummyhost.internal" in proc.stdout
    assert "DRY-RUN" in proc.stdout


def test_pilot_dry_run_inert():
    """ops/pilot.ps1 -DryRun rejimida o'zgarishsiz 0 bilan tugashi kerak."""
    script_path = os.path.join(ROOT_DIR, "ops", "pilot.ps1")
    env = os.environ.copy()
    env["SEED_INCLUDE_SERIES"] = "false"

    cmd = [
        "powershell",
        "-NoProfile",
        "-File",
        script_path,
        "-DryRun",
    ]
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert proc.returncode == 0, f"pilot -DryRun muvaffaqiyatsiz bo'ldi:\n{proc.stdout}\n{proc.stderr}"
    assert "DRY-RUN" in proc.stdout


def test_pilot_seed_include_series_guard():
    """SEED_INCLUDE_SERIES=true bo'lsa, ops/pilot.ps1 darhol to'xtashi kerak."""
    script_path = os.path.join(ROOT_DIR, "ops", "pilot.ps1")
    env = os.environ.copy()
    env["SEED_INCLUDE_SERIES"] = "true"

    cmd = [
        "powershell",
        "-NoProfile",
        "-File",
        script_path,
        "-DryRun",
    ]
    proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
    assert proc.returncode != 0, "pilot.ps1 SEED_INCLUDE_SERIES=true bo'lganda to'xtamadi!"
    assert "SEED_INCLUDE_SERIES" in proc.stdout


# -------------------------------------------------------------
# 3. ops/db_checks.py Unit Testlari
# -------------------------------------------------------------
def test_db_checks_host_sanitization():
    """Host sanitization parollar va foydalanuvchi nomini yashirishini tekshirish."""
    raw_url = "postgresql+asyncpg://admin_user:super_secret_password@ep-cool-fog-12345.eu-central-1.aws.neon.tech/kinochi"
    host = get_sanitized_host(raw_url)
    assert host == "ep-cool-fog-12345.eu-central-1.aws.neon.tech"
    assert "super_secret_password" not in host
    assert "admin_user" not in host

    assert get_sanitized_host(None) == "NONE"
    assert get_sanitized_host("") == "NONE"
    assert get_sanitized_host("not-a-valid-url:::") == "INVALID_URL"


def test_db_checks_normalize_async_url():
    """URL sxemasini asyncpg ga to'g'rilash tekshiruvi."""
    u1 = "postgresql://user:pass@host/db"
    assert normalize_async_url(u1) == "postgresql+asyncpg://user:pass@host/db"

    u2 = "postgres://user:pass@host/db"
    assert normalize_async_url(u2) == "postgresql+asyncpg://user:pass@host/db"

    u3 = "postgresql+asyncpg://user:pass@host/db"
    assert normalize_async_url(u3) == "postgresql+asyncpg://user:pass@host/db"


@pytest.mark.asyncio
async def test_db_checks_run_db_checks_mocked():
    """run_db_checks ning mock sessiya bilan ishlashi."""
    with patch.dict(os.environ, {"MOCK_TEST_DB": "postgresql://test_user:secret@mockhost/testdb"}):
        with patch("ops.db_checks.create_async_engine") as mock_engine_func:
            mock_engine = AsyncMock()
            mock_engine_func.return_value = mock_engine

            mock_session = AsyncMock()

            # Mock queries:
            # 1. alembic_version: e8f9a0b1c2d3
            # 2. columns default: 'pending'::character varying
            # 3. table counts: 0
            async def mock_execute(statement, *args, **kwargs):
                stmt_str = str(statement)
                mock_res = MagicMock()
                if "alembic_version" in stmt_str and "SELECT count" not in stmt_str:
                    mock_res.scalars.return_value.all.return_value = ["e8f9a0b1c2d3"]
                elif "information_schema.columns" in stmt_str:
                    mock_res.scalar.return_value = "'pending'::character varying"
                else:
                    mock_res.scalar.return_value = 0
                return mock_res

            mock_session.execute = AsyncMock(side_effect=mock_execute)

            with patch("ops.db_checks.async_sessionmaker", return_value=MagicMock(return_value=AsyncMock(__aenter__=AsyncMock(return_value=mock_session), __aexit__=AsyncMock()))):
                res = await run_db_checks(
                    env_var_name="MOCK_TEST_DB",
                    expected_alembic="e8f9a0b1c2d3",
                    expected_default="pending",
                    check_zero_media=True,
                    output_json=True,
                )
                assert res["ok"] is True
                assert res["host"] == "mockhost"
                assert res["alembic_version"] == "e8f9a0b1c2d3"
                assert res["publish_status_defaults"]["movies"] == "'pending'::character varying"


# -------------------------------------------------------------
# 4. ops/redis_flush_cache.py Unit Testlari
# -------------------------------------------------------------
def test_redis_host_sanitization():
    """Redis URL sanitization parollarni yashirishini tekshirish."""
    raw = "rediss://default:super_redis_token@eu1-cool-redis.upstash.io:6379/0"
    host = get_sanitized_redis_host(raw)
    assert host == "eu1-cool-redis.upstash.io"
    assert "super_redis_token" not in host
    assert "default" not in host
    assert get_sanitized_redis_host(None) == "NONE"


def test_redis_flush_cache_dry_run_and_confirm():
    """Redis cache flush: execute=False da o'chirmasligi, execute=True va YES da o'chirishi."""
    with patch("redis.Redis.from_url") as mock_from_url:
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client
        mock_client.scan_iter.return_value = [b"cache:item1", b"cache:item2"]

        # 1. execute=False -> o'chirmasligi kerak
        code = flush_cache_keys(
            redis_url="redis://localhost:6379/0",
            execute=False,
        )
        assert code == 0
        mock_client.delete.assert_not_called()

        # 2. execute=True lekin confirm noto'g'ri -> rad etilishi kerak
        code = flush_cache_keys(
            redis_url="redis://localhost:6379/0",
            execute=True,
            confirm_text="no",
        )
        assert code == 1
        mock_client.delete.assert_not_called()

        # 3. execute=True va confirm="YES" -> o'chirishi kerak
        code = flush_cache_keys(
            redis_url="redis://localhost:6379/0",
            execute=True,
            confirm_text="YES",
        )
        assert code == 0
        mock_client.delete.assert_called_once()
        args, kwargs = mock_client.delete.call_args
        assert set(args) == {b"cache:item1", b"cache:item2"}


# -------------------------------------------------------------
# 5. ops/new_telegram_session.py Unit Testlari
# -------------------------------------------------------------
def test_telegram_session_save_and_force():
    """Sessiyani faylga xavfsiz saqlash va force tekshiruvi."""
    with tempfile.TemporaryDirectory() as tmpdir:
        env_file = os.path.join(tmpdir, ".env.local")

        # 1. Yangi faylga yozish
        res = save_session_to_env_file(env_file, "session_string_one", force=False)
        assert res is True
        with open(env_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert 'TELEGRAM_STRING_SESSION="session_string_one"' in content

        # 2. Mavjud faylda force=False bo'lsa rad etilishi kerak
        res = save_session_to_env_file(env_file, "session_string_two", force=False)
        assert res is False
        with open(env_file, "r", encoding="utf-8") as f:
            content_after = f.read()
        assert "session_string_one" in content_after
        assert "session_string_two" not in content_after

        # 3. force=True bilan ustidan yozish
        res = save_session_to_env_file(env_file, "session_string_two", force=True)
        assert res is True
        with open(env_file, "r", encoding="utf-8") as f:
            content_forced = f.read()
        assert 'TELEGRAM_STRING_SESSION="session_string_two"' in content_forced
        assert "session_string_one" not in content_forced


def test_telegram_session_creation_mock():
    """create_telegram_session funksiyasining mock client bilan ishlashi."""
    mock_client_class = MagicMock()
    mock_client = MagicMock()
    mock_client_class.return_value = mock_client

    mock_client.is_user_authorized.return_value = False
    mock_client.session.save.return_value = "generated_secret_session_token"

    session = create_telegram_session(
        api_id=12345,
        api_hash="abcdef",
        phone="+998901234567",
        client_class=mock_client_class,
        code_callback=lambda: "12345",
    )
    assert session == "generated_secret_session_token"
    mock_client.connect.assert_called_once()
    mock_client.send_code_request.assert_called_once_with("+998901234567")
    mock_client.sign_in.assert_called_once_with("+998901234567", "12345")
    mock_client.disconnect.assert_called_once()
