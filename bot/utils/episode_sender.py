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
    translations = episode.get("translations", [])
    
    if not translations:
        return False
        
    caption = format_episode_caption(episode)
    keyboard = build_episode_keyboard(episode)
    
    item_code = episode.get("code")
    
    if len(translations) == 1:
        # Send video directly
        t = translations[0]
        from utils.movie_sender import send_video_translation
        return await send_video_translation(bot, chat_id, t, caption, reply_markup=keyboard)
    else:
        # Send keyboard to choose studio
        from keyboards.translations import get_translations_keyboard
        # The translation keyboard won't have navigation buttons in this step,
        # but they will be added when the video is sent in the callback.
        kb = get_translations_keyboard('E', item_code, translations)
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=f"🎬 <b>{episode.get('title') or episode.get('episode_number')}</b>\n\nQaysi tilda/studiyada ko'rishni xohlaysiz?",
                reply_markup=kb,
                parse_mode="HTML"
            )
            return True
        except TelegramBadRequest:
            return False
