from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from config import settings

def build_episode_keyboard(episode: dict) -> InlineKeyboardMarkup:
    """Builds inline keyboard for an episode."""
    rows = []
    
    # Row 1: Navigations
    nav_row = []
    prev_code = episode.get("prev_episode_code")
    next_code = episode.get("next_episode_code")
    
    if prev_code:
        nav_row.append(InlineKeyboardButton(text="◀ Oldingi qism", callback_data=f"ep_prev:{prev_code}"))
    if next_code:
        nav_row.append(InlineKeyboardButton(text="Keyingi qism ▶", callback_data=f"ep_next:{next_code}"))
        
    if nav_row:
        rows.append(nav_row)
        
    # Row 2: Menu and Info
    series_id = episode.get("series_id")
    info_row = [
        InlineKeyboardButton(text="Asosiy menu", callback_data="main_menu")
    ]
    if series_id:
        info_row.append(InlineKeyboardButton(text="Serial haqida", callback_data=f"series_info:{series_id}"))
        
    rows.append(info_row)
    
    return InlineKeyboardMarkup(inline_keyboard=rows)

def format_episode_caption(episode: dict) -> str:
    series_title = episode.get('series_title', 'Kechirasiz nomi topilmadi')
    display_code = episode.get('display_code', '')
    desc = episode.get('season_description') or ''
    
    if len(desc) > 150:
        desc = desc[:147] + "..."
        
    caption = f"🍿 <b>{series_title}</b>\n📌 {display_code}"
    if desc:
        caption += f"\n\n📝 <i>{desc}</i>"
        
    return caption

async def send_episode_to_user(bot: Bot, chat_id: int, episode: dict) -> bool:
    """
    Sends an episode video to the specified chat_id.
    """
    file_id = episode.get("telegram_file_id")
    storage_msg_id = episode.get("storage_channel_message_id")
    
    caption = format_episode_caption(episode)
    keyboard = build_episode_keyboard(episode)

    success = False
    
    # 1. Try sending via telegram_file_id
    if file_id:
        try:
            await bot.send_video(
                chat_id=chat_id, 
                video=file_id, 
                caption=caption, 
                parse_mode="HTML",
                reply_markup=keyboard
            )
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
                parse_mode="HTML",
                reply_markup=keyboard
            )
            success = True
        except TelegramBadRequest:
            pass

    return success
