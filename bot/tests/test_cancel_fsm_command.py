import sys
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

# Ensure mocks for backend modules not available in bot venv
sys.modules.setdefault("app", MagicMock())
sys.modules.setdefault("app.core", MagicMock())
sys.modules.setdefault("app.core.reviews", MagicMock())
sys.modules.setdefault("app.core.watch_history", MagicMock())

from aiogram.types import Message, User, Chat
from aiogram.fsm.context import FSMContext
from handlers.reviews import handle_review_comment, ReviewStates

@pytest.mark.asyncio
async def test_cancel_command_clears_review_state_without_saving():
    """
    BUG-005 Regression Test:
    When a user types /cancel in ReviewStates.waiting_for_comment,
    the bot MUST clear the state and MUST NOT save '/cancel' as a review comment!
    """
    message = MagicMock(spec=Message)
    message.text = "/cancel"
    message.from_user = MagicMock(spec=User)
    message.from_user.id = 12345
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 12345
    message.reply = AsyncMock()

    state = MagicMock(spec=FSMContext)
    state.get_state = AsyncMock(return_value=ReviewStates.waiting_for_comment.state)
    state.get_data = AsyncMock(return_value={"target_type": "m", "target_id": 100, "movie_id": 100, "rating": 9})
    state.clear = AsyncMock()

    with patch("handlers.reviews.submit_review", new_callable=AsyncMock) as mock_submit:
        await handle_review_comment(message, state)

        # Assertion: submit_review MUST NOT be called with "/cancel"
        mock_submit.assert_not_called()
        # State MUST be cleared
        state.clear.assert_awaited_once()
        # Bot should reply confirming cancellation
        message.reply.assert_awaited_once()
        reply_text = message.reply.call_args[0][0].lower()
        assert "bekor" in reply_text


@pytest.mark.asyncio
async def test_cancel_command_handler_with_and_without_state():
    """Verify /cancel command handler behaves correctly with or without state."""
    from handlers.reviews import cancel_command_handler

    # Case 1: Active state exists
    msg1 = MagicMock(spec=Message)
    msg1.reply = AsyncMock()
    state1 = MagicMock(spec=FSMContext)
    state1.get_state = AsyncMock(return_value="some_state")
    state1.clear = AsyncMock()

    await cancel_command_handler(msg1, state1)
    state1.clear.assert_awaited_once()
    msg1.reply.assert_awaited_once()
    assert "bekor qilindi" in msg1.reply.call_args[0][0].lower()

    # Case 2: No active state
    msg2 = MagicMock(spec=Message)
    msg2.reply = AsyncMock()
    state2 = MagicMock(spec=FSMContext)
    state2.get_state = AsyncMock(return_value=None)
    state2.clear = AsyncMock()

    await cancel_command_handler(msg2, state2)
    state2.clear.assert_not_called()
    msg2.reply.assert_awaited_once()
    assert "faol jarayon yo'q" in msg2.reply.call_args[0][0].lower()
