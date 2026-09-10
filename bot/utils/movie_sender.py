import logging
from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from config import settings
from keyboards.translations import get_translations_keyboard
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from app.core.watch_history import mark_movie_started, mark_episode_progress
from app.core.achievements import ACHIEVEMENTS
import html

async def notify_achievements(bot: Bot, chat_id: int, unlocked_codes: list[str]):
    if not unlocked_codes:
        return
    for code in unlocked_codes:
        text = ACHIEVEMENTS.get(code, "Yangi yutuq!")
        msg = f"🏆 <b>Tabriklaymiz! Yangi yutuq:</b>\n\n✨ {text}"
        try:
            await bot.send_message(chat_id, msg, parse_mode="HTML")
        except Exception as e:
            logging.warning(f"Failed to send achievement {code} to {chat_id}: {e}")

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
        
    safe_title = html.escape(movie.get('title', ''))
    safe_desc = html.escape(movie.get('description', ''))
    caption = f"🍿 <b>{safe_title}</b>\n\n{safe_desc}"
        
    # Check if this is an episode or movie by looking at fields
    # episodes have episode_number, movies have code but not episode_number
    item_type = 'E' if 'episode_number' in movie else 'M'
    item_code = movie.get("code")
    
    if len(translations) == 1:
        # Send video directly
        t = translations[0]
        item_id = movie.get("id")
        return await send_video_translation(bot, chat_id, t, caption, item_id=item_id, item_type=item_type)
    else:
        # Send keyboard to choose studio
        kb = get_translations_keyboard(item_type, item_code, translations)
        # Note: if it has a poster, we could send a photo, but here we just send text
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=f"🎬 <b>{safe_title}</b>\n\nQaysi tilda/studiyada ko'rishni xohlaysiz?",
                reply_markup=kb,
                parse_mode="HTML"
            )
            return True
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logging.warning(f"Failed to send keyboard for movie {item_code} to {chat_id}: {e}")
            return False

async def send_video_translation(bot: Bot, chat_id: int, translation: dict, caption: str, reply_markup=None, item_id: int = None, item_type: str = None) -> bool:
    file_id = translation.get("telegram_file_id")
    storage_msg_id = translation.get("storage_channel_message_id")
    
    success = False
    
    # 0. Append Watch History button for movies if item_id is present
    if item_id and item_type == 'M':
        btn = InlineKeyboardButton(text="✅ Ko'rib bo'ldim", callback_data=f"history_complete_movie_{item_id}")
        if reply_markup is None:
            reply_markup = InlineKeyboardMarkup(inline_keyboard=[[btn]])
        else:
            inline_kb = reply_markup.inline_keyboard.copy()
            inline_kb.append([btn])
            reply_markup = InlineKeyboardMarkup(inline_keyboard=inline_kb)

    # 1. Try sending via telegram_file_id
    if file_id:
        try:
            await bot.send_video(chat_id=chat_id, video=file_id, caption=caption, parse_mode="HTML", reply_markup=reply_markup)
            success = True
        except (TelegramBadRequest, TelegramForbiddenError) as e:
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
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logging.warning(f"Failed to copy message {storage_msg_id} from storage to {chat_id}: {e}")

    # Log watch history if successfully sent
    if success and item_id:
        if item_type == 'M':
            await mark_movie_started(chat_id, item_id)
        elif item_type == 'E':
            unlocked = await mark_episode_progress(chat_id, item_id)
            if unlocked:
                await notify_achievements(bot, chat_id, unlocked)
            
    return success
