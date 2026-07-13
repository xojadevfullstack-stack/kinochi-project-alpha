from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.exceptions import TelegramBadRequest
from services.api_client import api_client
from typing import Optional
import html

async def send_movie_info(bot: Bot, chat_id: int, movie: dict, edit_message_id: Optional[int] = None):
    """Sends movie info card with 'Ko'rish' button."""
    title = html.escape(movie.get("title", "Nomsiz kino"))
    desc = html.escape(movie.get("description") or "Ma'lumot mavjud emas.")
    year = movie.get("release_year")
    rating = movie.get("imdb_rating")
    poster_url = movie.get("poster_url")
    code = movie.get("code")
    
    caption = f"🎬 <b>{title}</b>\n\n"
    if year: caption += f"📅 <b>Yil:</b> {year}\n"
    if rating: caption += f"⭐ <b>IMDb:</b> {rating}\n"
    caption += f"\n📝 <b>Tavsif:</b> {desc}"
    
    # Cap description length to avoid Telegram limits
    if len(caption) > 1000:
        caption = caption[:997] + "..."
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶ Ko'rish", callback_data=f"watch_m_{code}")],
        [
            InlineKeyboardButton(text="◀️ Ortga", callback_data="menu_movies"),
            InlineKeyboardButton(text="❌ Yopish", callback_data="delete_msg")
        ]
    ])
    
    try:
        if edit_message_id:
            if poster_url:
                try:
                    await bot.edit_message_media(
                        chat_id=chat_id,
                        message_id=edit_message_id,
                        media=InputMediaPhoto(media=poster_url, caption=caption, parse_mode="HTML"),
                        reply_markup=keyboard
                    )
                except TelegramBadRequest:
                    # Fallback if poster is invalid or media cannot be edited
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=edit_message_id,
                        text=caption,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
            else:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=edit_message_id,
                    text=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
        else:
            if poster_url:
                try:
                    await bot.send_photo(chat_id=chat_id, photo=poster_url, caption=caption, parse_mode="HTML", reply_markup=keyboard)
                except TelegramBadRequest:
                    # Fallback if poster is invalid
                    await bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML", reply_markup=keyboard)
            else:
                await bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML", reply_markup=keyboard)
        return True
    except TelegramBadRequest as e:
        print(f"Error sending movie info: {e}")
        return False

async def send_series_info(bot: Bot, chat_id: int, series: dict, edit_message_id: Optional[int] = None):
    """Sends series info card with seasons buttons."""
    title = html.escape(series.get("title", "Nomsiz serial"))
    desc = html.escape(series.get("description") or "Ma'lumot mavjud emas.")
    year = series.get("release_year")
    rating = series.get("imdb_rating")
    poster_url = series.get("poster_url")
    series_id = series.get("id")
    
    seasons = series.get("seasons", [])
    
    caption = f"🎬 <b>{title}</b>\n\n"
    if year: caption += f"📅 <b>Yil:</b> {year}\n"
    if rating: caption += f"⭐ <b>IMDb:</b> {rating}\n"
    caption += f"\n📝 <b>Tavsif:</b> {desc}\n\n📚 <b>Fasllar:</b> Quyidan faslni tanlang:"
    
    if len(caption) > 1000:
        caption = caption[:997] + "..."
    
    # Build seasons keyboard
    rows = []
    current_row = []
    
    # Sort seasons by number
    seasons = sorted(seasons, key=lambda s: s.get("season_number", 0))
    
    for s in seasons:
        s_id = s.get("id")
        s_num = s.get("season_number")
        current_row.append(InlineKeyboardButton(text=f"{s_num}-Mavsum", callback_data=f"show_season_{series_id}_{s_id}"))
        if len(current_row) == 2: # 2 buttons per row
            rows.append(current_row)
            current_row = []
            
    if current_row:
        rows.append(current_row)
        
    rows.append([
        InlineKeyboardButton(text="◀️ Ortga", callback_data="menu_series"),
        InlineKeyboardButton(text="❌ Yopish", callback_data="delete_msg")
    ])
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
    
    try:
        if edit_message_id:
            if poster_url:
                try:
                    await bot.edit_message_media(
                        chat_id=chat_id,
                        message_id=edit_message_id,
                        media=InputMediaPhoto(media=poster_url, caption=caption, parse_mode="HTML"),
                        reply_markup=keyboard
                    )
                except TelegramBadRequest:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=edit_message_id,
                        text=caption,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
            else:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=edit_message_id,
                    text=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
        else:
            if poster_url:
                try:
                    await bot.send_photo(chat_id=chat_id, photo=poster_url, caption=caption, parse_mode="HTML", reply_markup=keyboard)
                except TelegramBadRequest:
                    await bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML", reply_markup=keyboard)
            else:
                await bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML", reply_markup=keyboard)
        return True
    except TelegramBadRequest as e:
        print(f"Error sending series info: {e}")
        return False
        
async def send_season_info(bot: Bot, chat_id: int, season: dict, edit_message_id: Optional[int] = None, series_poster: str = None):
    """Sends season info card with episodes buttons."""
    s_num = season.get("season_number", 0)
    title = html.escape(season.get("title") or f"{s_num}-Mavsum")
    desc = html.escape(season.get("description") or "")
    poster_url = season.get("poster_url") or series_poster
    season_id = season.get("id")
    series_id = season.get("series_id")
    
    episodes = season.get("episodes", [])
    
    caption = f"📚 <b>{title}</b>\n\n"
    if desc: caption += f"📝 <i>{desc}</i>\n\n"
    caption += "▶️ <b>Qismni tanlang:</b>"
    
    if len(caption) > 1000:
        caption = caption[:997] + "..."
    
    # Build episodes keyboard
    rows = []
    current_row = []
    
    # Sort episodes by number
    episodes = sorted(episodes, key=lambda e: e.get("episode_number", 0))
    
    for e in episodes:
        e_num = e.get("episode_number")
        e_code = e.get("code")
        current_row.append(InlineKeyboardButton(text=f"{e_num}-qism", callback_data=f"watch_e_{e_code}"))
        if len(current_row) == 4: # 4 buttons per row for episodes
            rows.append(current_row)
            current_row = []
            
    if current_row:
        rows.append(current_row)
        
    rows.append([
        InlineKeyboardButton(text="◀️ Ortga", callback_data=f"back_to_series:{series_id}"),
        InlineKeyboardButton(text="❌ Yopish", callback_data="delete_msg")
    ])
        
    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
    
    try:
        if edit_message_id:
            if poster_url:
                try:
                    await bot.edit_message_media(
                        chat_id=chat_id,
                        message_id=edit_message_id,
                        media=InputMediaPhoto(media=poster_url, caption=caption, parse_mode="HTML"),
                        reply_markup=keyboard
                    )
                except TelegramBadRequest:
                    await bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=edit_message_id,
                        text=caption,
                        parse_mode="HTML",
                        reply_markup=keyboard
                    )
            else:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=edit_message_id,
                    text=caption,
                    parse_mode="HTML",
                    reply_markup=keyboard
                )
        else:
            if poster_url:
                try:
                    await bot.send_photo(chat_id=chat_id, photo=poster_url, caption=caption, parse_mode="HTML", reply_markup=keyboard)
                except TelegramBadRequest:
                    await bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML", reply_markup=keyboard)
            else:
                await bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML", reply_markup=keyboard)
        return True
    except TelegramBadRequest as e:
        print(f"Error sending season info: {e}")
        return False
