import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from config import settings
from keyboards.translations import get_translations_keyboard

async def send_movie_to_user(bot: Bot, chat_id: int, movie: dict) -> bool:
    """
    Sends a movie video to the specified chat_id.
    Attempts to send via telegram_file_id first, then falls back to copying
    from the storage channel if available.
    
    If multiple translations exist, sends a keyboard to select the studio.
    
    Returns True if successfully sent (or keyboard sent), False otherwise.
    """
    translations = movie.get("translations", [])
    
    if not translations:
        return False
        
    caption = f"🍿 <b>{movie.get('title')}</b>\n\n{movie.get('description') or ''}"
        
    # Check if this is an episode or movie by looking at fields
    # episodes have episode_number, movies have code but not episode_number
    item_type = 'E' if 'episode_number' in movie else 'M'
    item_code = movie.get("code")
    
    if len(translations) == 1:
        # Send video directly
        t = translations[0]
        return await send_video_translation(bot, chat_id, t, caption)
    else:
        # Send keyboard to choose studio
        kb = get_translations_keyboard(item_type, item_code, translations)
        # Note: if it has a poster, we could send a photo, but here we just send text
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=f"🎬 <b>{movie.get('title')}</b>\n\nQaysi tilda/studiyada ko'rishni xohlaysiz?",
                reply_markup=kb,
                parse_mode="HTML"
            )
            return True
        except TelegramBadRequest as e:
            logging.warning(f"Failed to send keyboard for movie {item_code} to {chat_id}: {e}")
            return False

async def send_video_translation(bot: Bot, chat_id: int, translation: dict, caption: str, reply_markup=None) -> bool:
    file_id = translation.get("telegram_file_id")
    storage_msg_id = translation.get("storage_channel_message_id")
    
    success = False
    
    # 1. Try sending via telegram_file_id
    if file_id:
        try:
            await bot.send_video(chat_id=chat_id, video=file_id, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
            success = True
        except TelegramBadRequest as e:
            logging.warning(f"Failed to send video via file_id {file_id} to {chat_id}: {e}")
            
    # 2. Fallback to copy from storage channel
    if not success and storage_msg_id and settings.STORAGE_CHANNEL_ID:
        try:
            await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=settings.STORAGE_CHANNEL_ID,
                message_id=storage_msg_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=reply_markup
            )
            success = True
        except TelegramBadRequest as e:
            logging.warning(f"Failed to copy message {storage_msg_id} from storage to {chat_id}: {e}")

    return success
