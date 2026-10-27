import pytest
import os
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.bot_status import set_bot_alive, is_bot_alive

@pytest.mark.asyncio
async def test_health_endpoint_includes_bot_alive():
    """GET /health endpointi bot_alive holatini to'g'ri qaytarishi kerak."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Default holatda bot_alive False bo'lishi kerak
        set_bot_alive(False)
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert "bot_alive" in data
        assert data["bot_alive"] is False

        # Bot ishga tushganda bot_alive True bo'lishi kerak
        set_bot_alive(True)
        res2 = await client.get("/health")
        assert res2.status_code == 200
        assert res2.json()["bot_alive"] is True
        
        # Test yakunida holatni tozalash
        set_bot_alive(False)


@pytest.mark.asyncio
async def test_supervised_run_bot_retries_and_exits_nonzero():
    """supervised_run_bot() xatolik yuz berganda exponential backoff bilan qayta urinadi va oxirida non-zero (sys.exit(1)) bilan tugaydi."""
    import run

    call_count = 0
    async def failing_run_bot():
        nonlocal call_count
        call_count += 1
        raise RuntimeError(f"Simulated Telegram Polling Failure {call_count}")

    with patch.dict(os.environ, {"MAX_BOT_RESTARTS": "3", "BOT_RESTART_BASE_DELAY": "0.01"}), \
         patch("bot.main.run_bot", side_effect=failing_run_bot), \
         patch("sys.exit") as mock_exit, \
         patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:

        await run.supervised_run_bot()

        assert call_count == 3
        # sys.exit(1) non-zero bilan chaqirilgan bo'lishi shart
        mock_exit.assert_called_with(1)
        # 2 marta qayta urinish oralig'ida sleep chaqirilgan bo'lishi kerak
        assert mock_sleep.await_count == 2


@pytest.mark.asyncio
async def test_supervised_run_bot_clean_exit():
    """run_bot normal yakunlanganda supervised_run_bot ham toza chiqadi va sys.exit chaqirilmaydi."""
    import run

    with patch("bot.main.run_bot", new_callable=AsyncMock) as mock_bot, \
         patch("sys.exit") as mock_exit:
        mock_bot.return_value = None

        await run.supervised_run_bot()

        mock_bot.assert_awaited_once()
        mock_exit.assert_not_called()
        assert is_bot_alive() is False


def test_run_py_no_return_exceptions_masking():
    """run.py dagi main() funksiyasida return_exceptions=True masking bo'lmasligi kerak."""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    run_py_path = os.path.join(repo_root, "run.py") if os.path.exists(os.path.join(repo_root, "run.py")) else "run.py"
    with open(run_py_path, "r", encoding="utf-8") as f:
        content = f.read()

    assert "return_exceptions=True" not in content, (
        "run.py da return_exceptions=True qolgan! Exception masking olib tashlanishi shart."
    )


@pytest.mark.asyncio
async def test_bot_startup_logs_pending_and_respects_drop_pending_updates():
    """bot/main.py da kutilayotgan yangilanishlar soni log qilinishi va BOT_DROP_PENDING_UPDATES ga rioya qilinishi tekshiriladi."""
    from bot import main as bot_main

    mock_bot = MagicMock()
    mock_webhook_info = MagicMock()
    mock_webhook_info.pending_update_count = 42
    mock_bot.get_webhook_info = AsyncMock(return_value=mock_webhook_info)
    mock_bot.delete_webhook = AsyncMock()
    mock_bot.set_chat_menu_button = AsyncMock()
    mock_bot.session = MagicMock()
    mock_bot.session.close = AsyncMock()

    mock_dp = MagicMock()
    mock_dp.start_polling = AsyncMock(return_value=None)
    mock_dp.resolve_used_update_types = MagicMock(return_value=[])

    with patch.dict(os.environ, {"BOT_DROP_PENDING_UPDATES": "false"}), \
         patch("bot.main.Bot", return_value=mock_bot), \
         patch("bot.main.Dispatcher", return_value=mock_dp), \
         patch("bot.main.api_client.close", new_callable=AsyncMock):

        await bot_main.run_bot()

        mock_bot.get_webhook_info.assert_awaited_once()
        # Default False bo'yicha delete_webhook chaqirilgan
        mock_bot.delete_webhook.assert_awaited_once_with(drop_pending_updates=False)

    # Endi BOT_DROP_PENDING_UPDATES=True bo'lganda tekshiramiz
    mock_bot.delete_webhook.reset_mock()
    with patch.dict(os.environ, {"BOT_DROP_PENDING_UPDATES": "true"}), \
         patch("bot.main.Bot", return_value=mock_bot), \
         patch("bot.main.Dispatcher", return_value=mock_dp), \
         patch("bot.main.api_client.close", new_callable=AsyncMock):

        await bot_main.run_bot()

        mock_bot.delete_webhook.assert_awaited_once_with(drop_pending_updates=True)
