from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from handlers.smm_admin import handle_smm_callback


@pytest.mark.asyncio
async def test_smm_callback_requires_admin_and_executes_actions(monkeypatch):
    monkeypatch.setenv("ADMIN_IDS", "111222")

    # Non-admin must be blocked
    cb_unauth = MagicMock()
    cb_unauth.from_user = MagicMock(id=999999)
    cb_unauth.data = "smm_approve:7"
    cb_unauth.answer = AsyncMock()
    with patch("handlers.smm_admin.api_client.act_on_smm_job", new=AsyncMock()) as mock_act:
        await handle_smm_callback(cb_unauth)
    mock_act.assert_not_awaited()
    assert cb_unauth.answer.await_args_list[0].kwargs.get("show_alert") is True

    # Authorized admin triggers approve, publish, reject cleanly
    for data, expected_action, expected_pub in [
        ("smm_approve:7", "approve", False),
        ("smm_publish:7", "approve", True),
        ("smm_reject:7", "reject", False),
    ]:
        cb = MagicMock()
        cb.from_user = MagicMock(id=111222)
        cb.data = data
        cb.answer = AsyncMock()
        cb.message = MagicMock()
        cb.message.edit_reply_markup = AsyncMock()
        cb.message.reply = AsyncMock()
        with patch("handlers.smm_admin.api_client.act_on_smm_job", new=AsyncMock(return_value={"status": "ok"})) as mock_act:
            await handle_smm_callback(cb)
        mock_act.assert_awaited_once_with(7, action=expected_action, publish_now=expected_pub, telegram_user_id=111222)
        cb.message.edit_reply_markup.assert_awaited_once()
        cb.message.reply.assert_awaited_once()


@pytest.mark.asyncio
async def test_smm_callback_falls_back_to_backend_db_admin_when_env_empty(monkeypatch):
    monkeypatch.delenv("ADMIN_IDS", raising=False)
    monkeypatch.delenv("SMM_ADMIN_TELEGRAM_ID", raising=False)

    cb = MagicMock()
    cb.from_user = MagicMock(id=1990156236)
    cb.data = "smm_publish:3"
    cb.answer = AsyncMock()
    cb.message = MagicMock()
    cb.message.edit_reply_markup = AsyncMock()
    cb.message.reply = AsyncMock()

    with patch("handlers.smm_admin.api_client.act_on_smm_job", new=AsyncMock(return_value={"status": "publishing"})) as mock_act:
        await handle_smm_callback(cb)

    mock_act.assert_awaited_once_with(3, action="approve", publish_now=True, telegram_user_id=1990156236)
    cb.message.reply.assert_awaited_once()
