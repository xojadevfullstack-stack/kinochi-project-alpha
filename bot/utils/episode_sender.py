from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest
from config import settings
import html

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
        
    # Row 2: Complete and Rate buttons
    ep_id = episode.get("id")
    if ep_id:
        rows.append([
            InlineKeyboardButton(text="✅ Ko'rib bo'ldim", callback_data=f"history_complete_ep_{ep_id}"),
            InlineKeyboardButton(text="⭐ Baholash", callback_data=f"rate_ep_{ep_id}")
        ])

    # Row 3: Info
    series_id = episode.get("series_id")
    if series_id:
        rows.append([InlineKeyboardButton(text="Serial haqida", callback_data=f"series_info:{series_id}")])
    
    return InlineKeyboardMarkup(inline_keyboard=rows)

def format_episode_caption(episode: dict) -> str:
    series_title = html.escape(episode.get('series_title', 'Kechirasiz nomi topilmadi'))
    display_code = episode.get('display_code', '')
    desc = html.escape(episode.get('season_description') or '')
    
    if len(desc) > 150:
        desc = desc[:147] + "..."
        
    # display_code is usually S1-CH1. We can format it nicely.
    season_num = episode.get("season_number", "?")
    episode_num = episode.get("episode_number", "?")
    
    if season_num != "?" and episode_num != "?":
        display_text = f"📌 <b>{season_num}-mavsum, {episode_num}-qism</b>"
    else:
        display_text = f"📌 {display_code}"
        
    caption = f"🍿 <b>{series_title}</b>\n{display_text}"
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
        item_id = episode.get("id")
        return await send_video_translation(bot, chat_id, t, caption, reply_markup=keyboard, item_id=item_id, item_type='E')
    else:
        # Send keyboard to choose studio
        from keyboards.translations import get_translations_keyboard
        # The translation keyboard won't have navigation buttons in this step,
        # but they will be added when the video is sent in the callback.
        kb = get_translations_keyboard('E', item_code, translations)
        try:
            safe_title = html.escape(episode.get('title') or str(episode.get('episode_number', '')))
            await bot.send_message(
                chat_id=chat_id,
                text=f"🎬 <b>{safe_title}</b>\n\nQaysi tilda/studiyada ko'rishni xohlaysiz?",
                reply_markup=kb,
                parse_mode="HTML"
            )
            return True
        except TelegramBadRequest:
            return False
