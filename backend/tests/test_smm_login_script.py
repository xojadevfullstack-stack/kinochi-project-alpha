import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


def test_upsert_env_key_preserves_scraper_session_and_updates_smm_key():
    from scripts.smm_telegram_login import upsert_env_key

    original = (
        "TELEGRAM_API_ID=12345\n"
        "TELEGRAM_STRING_SESSION=scraper_primary_session\n"
        "OTHER_VAR=hello\n"
    )
    added = upsert_env_key(original, "SMM_TELEGRAM_STRING_SESSION", "smm_session_v1")
    assert "TELEGRAM_STRING_SESSION=scraper_primary_session" in added
    assert "SMM_TELEGRAM_STRING_SESSION=smm_session_v1" in added

    updated = upsert_env_key(added, "SMM_TELEGRAM_STRING_SESSION", "smm_session_v2")
    assert updated.count("SMM_TELEGRAM_STRING_SESSION=") == 1
    assert "SMM_TELEGRAM_STRING_SESSION=smm_session_v2" in updated
    assert "TELEGRAM_STRING_SESSION=scraper_primary_session" in updated


def test_resolve_api_credentials_reads_env_without_hardcoded_secrets(monkeypatch):
    from scripts.smm_telegram_login import resolve_api_credentials

    monkeypatch.setenv("TELEGRAM_API_ID", "998877")
    monkeypatch.setenv("TELEGRAM_API_HASH", "hash_from_env")
    api_id, api_hash = resolve_api_credentials()
    assert api_id == 998877
    assert api_hash == "hash_from_env"

    monkeypatch.delenv("TELEGRAM_API_ID", raising=False)
    monkeypatch.delenv("TELEGRAM_API_HASH", raising=False)
    with pytest.raises(ValueError, match="TELEGRAM_API_ID"):
        resolve_api_credentials()


@pytest.mark.asyncio
async def test_verify_storage_channel_access_reports_ok_and_missing_access():
    from scripts.smm_telegram_login import verify_storage_channel_access

    client_ok = MagicMock()
    entity = MagicMock(title="Kinochi Storage")
    client_ok.get_entity = AsyncMock(return_value=entity)
    ok, info = await verify_storage_channel_access(client_ok, -1001234567890)
    assert ok is True
    assert "Kinochi Storage" in info

    client_fail = MagicMock()
    client_fail.get_entity = AsyncMock(side_effect=PermissionError("ChannelPrivateError"))
    ok2, info2 = await verify_storage_channel_access(client_fail, -1001234567890)
    assert ok2 is False
    assert "ChannelPrivateError" in info2
