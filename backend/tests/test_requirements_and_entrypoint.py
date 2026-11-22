import asyncio
import builtins
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]


def test_root_requirements_contains_smm_vision_and_env_dependencies():
    req_text = (ROOT_DIR / "requirements.txt").read_text(encoding="utf-8").lower()
    assert "opencv-python-headless" in req_text
    assert "numpy" in req_text
    assert "python-dotenv" in req_text


@pytest.mark.asyncio
async def test_safe_run_smm_worker_isolates_import_errors_without_crashing():
    import run as app_run

    real_import = builtins.__import__

    def failing_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "scraper.smm_worker":
            raise ModuleNotFoundError("No module named 'cv2'")
        return real_import(name, globals, locals, fromlist, level)

    with (
        patch("builtins.__import__", side_effect=failing_import),
        patch.object(app_run.asyncio, "sleep", new=AsyncMock(side_effect=asyncio.CancelledError)),
    ):
        with pytest.raises(asyncio.CancelledError):
            await app_run.safe_run_smm_worker()
