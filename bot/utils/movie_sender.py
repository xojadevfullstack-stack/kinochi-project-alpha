from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from config import settings

async def send_movie_to_user(bot: Bot, chat_id: int, movie: dict) -> bool:
    """
    Sends a movie video to the specified chat_id.
    Attempts to send via telegram_file_id first, then falls back to copying
    from the storage channel if available.
    
    Returns True if successfully sent, False otherwise.
    """
    file_id = movie.get("telegram_file_id")
    storage_msg_id = movie.get("storage_channel_message_id")
    caption = f"🍿 <b>{movie.get('title')}</b>\n\n{movie.get('description') or ''}"

    success = False
    
    # 1. Try sending via telegram_file_id
    if file_id:
        try:
            await bot.send_video(chat_id=chat_id, video=file_id, caption=caption, parse_mode="HTML")
            success = True
        except TelegramBadRequest:
            pass
            
    # 2. Fallback to copy from storage channel
    if not success and storage_msg_id and settings.STORAGE_CHANNEL_ID:
        try:
            await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=settings.STORAGE_CHANNEL_ID,
                message_id=storage_msg_id,
                caption=caption,
                parse_mode="HTML"
            )
            success = True
        except TelegramBadRequest:
            pass

    return success
