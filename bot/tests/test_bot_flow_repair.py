import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from aiogram.types import Message, User, Chat, CallbackQuery
from handlers.start import cmd_start
from handlers.search import handle_search_query

@pytest.mark.asyncio
async def test_bot_issue_001_welcome_message_mediaplus_branding():
    """BOT-ISSUE-001: Start command welcome message must greet with 'MediaPlus' branding."""
    message = MagicMock(spec=Message)
    message.from_user = User(id=12345, is_bot=False, first_name="TestUser", username="testuser")
    message.answer = AsyncMock()
    
    command = MagicMock()
    command.args = None  # No deep link arguments
    
    with patch("services.api_client.api_client.register_user", new=AsyncMock(return_value={"id": 1, "is_banned": False})):
        await cmd_start(message, command)
    
    assert message.answer.called, "cmd_start did not call message.answer"
    welcome_text = message.answer.call_args[0][0]
    
    assert "MediaPlus" in welcome_text, f"Welcome message must contain 'MediaPlus': {welcome_text}"


@pytest.mark.asyncio
async def test_bot_issue_002_recommendation_text_query_returns_real_menu():
    """BOT-ISSUE-002: Sending '🎲 Tavsiya kino' or '🎲 Tavsiya' must NOT return fake 'Tez kunda' placeholder.
    It must display the real recommendation menu with actionable choices.
    """
    message = MagicMock(spec=Message)
    message.from_user = User(id=12345, is_bot=False, first_name="TestUser", username="testuser")
    message.chat = Chat(id=12345, type="private")
    message.text = "🎲 Tavsiya kino"
    message.answer = AsyncMock()

    with patch("services.api_client.api_client.get_pages", new=AsyncMock(return_value={"items": []})):
        await handle_search_query(message)

    assert message.answer.called, "handle_search_query did not call message.answer"
    reply_text = message.answer.call_args[0][0]
    
    # Must NOT be a fake 'Tez kunda' placeholder
    assert "Tez kunda" not in reply_text, f"Search handler returned fake placeholder 'Tez kunda': {reply_text}"
    assert "tayyorlayapmiz" not in reply_text
    
    # Must provide recommendation options / keyboard
    reply_markup = message.answer.call_args[1].get("reply_markup")
    assert reply_markup is not None, "Real recommendation menu must supply an inline keyboard markup"
    
    # Check that callback buttons exist for recommendation categories
    all_callbacks = [
        btn.callback_data for row in reply_markup.inline_keyboard for btn in row if btn.callback_data
    ]
    assert any("rec_cat:" in cb for cb in all_callbacks), f"No rec_cat buttons found in markup: {all_callbacks}"
