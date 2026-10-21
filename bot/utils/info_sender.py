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
    kinochi_rating = movie.get("kinochi_rating")
    kinochi_votes = movie.get("kinochi_votes_count", 0)
    poster_url = movie.get("poster_url")
    code = movie.get("code")
    
    is_18 = bool(movie.get("is_18_plus"))
    caption = ""
    if is_18:
        caption += "🔞 <b>18+ Kattalar uchun</b>\n\n"
    caption += f"🎬 <b>{title}</b>\n\n"
    if code: caption += f"🔑 <b>Kino kodi:</b> <code>{code}</code>\n"
    if year: caption += f"📅 <b>Yil:</b> {year}\n"
    if rating: 
        caption += f"⭐ <b>IMDb:</b> {rating} / 10\n"
    else:
        caption += f"⭐ <b>IMDb:</b> N/A\n"

    if kinochi_rating:
        caption += f"💜 <b>Kinochi:</b> {kinochi_rating:.1f} / 10 ({kinochi_votes} ta ovoz)\n"
    else:
        caption += f"💜 <b>Kinochi:</b> Yangi\n"

    # Manba brendingi (Source branding)
    src_type = (movie.get("source_type") or "").lower()
    custom_src = movie.get("custom_source_name")
    if custom_src:
        caption += f"🏷️ <b>Manba:</b> {html.escape(custom_src)}\n"
    elif src_type == "uzmovi":
        caption += "🏷️ <b>Manba:</b> UzMovi\n"
    elif src_type == "asilmedia":
        caption += "🏷️ <b>Manba:</b> AsilMedia\n"
    elif src_type == "anitoob":
        caption += "🏷️ <b>Manba:</b> AniToob\n"
    elif src_type == "animeelar":
        caption += "🏷️ <b>Manba:</b> Animeelar\n"

    caption += f"\n📝 <b>Tavsif:</b> {desc}"
    
    # Cap description length to avoid Telegram limits
    if len(caption) > 1000:
        caption = caption[:997] + "..."
    
    trailer_url = movie.get("trailer_url")
    
    # Franshizaning boshqa qismlarini tekshirish
    franchise = None
    if code:
        try:
            franchise = await api_client.get_movie_franchise_context(code)
        except Exception:
            franchise = None

    buttons = [
        [InlineKeyboardButton(text="▶ Ko'rish", callback_data=f"watch_m_{code}")],
    ]

    if franchise and franchise.get("timeline_items") and len(franchise["timeline_items"]) > 1:
        total_parts = len(franchise["timeline_items"])
        col_id = franchise.get("collection_id")
        col_name = franchise.get("collection_name", "Franshiza")
        buttons.append([
            InlineKeyboardButton(
                text=f"📚 {col_name} ({total_parts} ta qism)",
                callback_data=f"franchise_m_{code}"
            )
        ])
        if col_id:
            try:
                is_sub = await api_client.check_collection_subscription(col_id, chat_id)
            except Exception:
                is_sub = False
            sub_icon = "🔕" if is_sub else "🔔"
            sub_text = "Obunani bekor qilish" if is_sub else f"Obuna: {col_name[:15]}"
            buttons.append([
                InlineKeyboardButton(
                    text=f"{sub_icon} {sub_text}",
                    callback_data=f"sub_col_{col_id}_{code}"
                )
            ])

    buttons.append([
        InlineKeyboardButton(text="⭐ Baholash", callback_data=f"rate_m_{code}"),
        InlineKeyboardButton(text="💬 Fikrlar", callback_data=f"reviews_m_{code}")
    ])
    
    if trailer_url:
        buttons.append([InlineKeyboardButton(text="🎬 Treyler", callback_data=f"trailer_m_{code}")])
        
    buttons.append([InlineKeyboardButton(text="⚠️ Xatolikni bildirish", callback_data=f"report_m_{code}")])
    buttons.append([
        InlineKeyboardButton(text="◀️ Ortga", callback_data="menu_catalog"),
        InlineKeyboardButton(text="❌ Yopish", callback_data="delete_msg")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
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
    kinochi_rating = series.get("kinochi_rating")
    kinochi_votes = series.get("kinochi_votes_count", 0)
    poster_url = series.get("poster_url")
    series_id = series.get("id")
    
    seasons = series.get("seasons", [])
    
    is_18 = bool(series.get("is_18_plus"))
    caption = ""
    if is_18:
        caption += "🔞 <b>18+ Kattalar uchun</b>\n\n"
    caption += f"🎬 <b>{title}</b>\n\n"
    if series_id: caption += f"🔑 <b>Serial kodi:</b> <code>s_{series_id}</code>\n"
    if year: caption += f"📅 <b>Yil:</b> {year}\n"
    if rating: 
        caption += f"⭐ <b>IMDb:</b> {rating} / 10\n"
    else:
        caption += f"⭐ <b>IMDb:</b> N/A\n"

    if kinochi_rating:
        caption += f"💜 <b>Kinochi:</b> {kinochi_rating:.1f} / 10 ({kinochi_votes} ta ovoz)\n"
    else:
        caption += f"💜 <b>Kinochi:</b> Yangi\n"

    # Manba brendingi (Source branding)
    src_type = (series.get("source_type") or "").lower()
    custom_src = series.get("custom_source_name")
    if custom_src:
        caption += f"🏷️ <b>Manba:</b> {html.escape(custom_src)}\n"
    elif src_type == "uzmovi":
        caption += "🏷️ <b>Manba:</b> UzMovi\n"
    elif src_type == "asilmedia":
        caption += "🏷️ <b>Manba:</b> AsilMedia\n"
    elif src_type == "anitoob":
        caption += "🏷️ <b>Manba:</b> AniToob\n"
    elif src_type == "animeelar":
        caption += "🏷️ <b>Manba:</b> Animeelar\n"

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

    # Check series watch progress and add "Ko'rib bo'ldim" button
    try:
        from app.core.watch_history import get_series_watch_status
        status_info = await get_series_watch_status(chat_id, series_id)
        if status_info.get("is_fully_completed"):
            rows.append([InlineKeyboardButton(text="✅ To'liq ko'rilgan", callback_data="ignore_history")])
        else:
            rows.append([InlineKeyboardButton(text="✅ Ko'rib bo'ldim", callback_data=f"history_complete_series_{series_id}")])
    except Exception as e:
        rows.append([InlineKeyboardButton(text="✅ Ko'rib bo'ldim", callback_data=f"history_complete_series_{series_id}")])
        
    try:
        is_sub = await api_client.check_series_subscription(series_id, chat_id)
    except Exception:
        is_sub = False
    sub_text = "🔕 Obunani bekor qilish" if is_sub else "🔔 Yangi qismlarga obuna bo'lish"
    rows.append([InlineKeyboardButton(text=sub_text, callback_data=f"sub_series_{series_id}")])

    rows.append([
        InlineKeyboardButton(text="⭐ Baholash", callback_data=f"rate_s_{series_id}"),
        InlineKeyboardButton(text="💬 Fikrlar", callback_data=f"reviews_s_{series_id}")
    ])

    trailer_url = series.get("trailer_url")
    
    if trailer_url:
        rows.append([InlineKeyboardButton(text="🎬 Treyler", callback_data=f"trailer_s_{series_id}")])
        
    rows.append([InlineKeyboardButton(text="⚠️ Xatolikni bildirish", callback_data=f"report_s_{series_id}")])
    rows.append([
        InlineKeyboardButton(text="◀️ Ortga", callback_data="menu_catalog"),
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
        InlineKeyboardButton(text="◀️ Serialga qaytish", callback_data=f"back_to_series:{series_id}"),
        InlineKeyboardButton(text="📂 Katalog", callback_data="menu_catalog")
    ])
    rows.append([
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


async def send_collection_info(bot: Bot, chat_id: int, collection: dict, edit_message_id: Optional[int] = None) -> bool:
    """Sends collection / franchise info card with all its timeline parts."""
    col_id = collection.get("id")
    name = html.escape(collection.get("name", "To'plam"))
    desc = html.escape(collection.get("description") or "Kinokoinotning barcha qismlarini to'liq ketma-ketlikda tomosha qiling.")
    poster_url = collection.get("poster_url") or collection.get("banner_url")
    items = collection.get("items", [])
    total = len(items)

    try:
        is_sub = await api_client.check_collection_subscription(col_id, chat_id)
    except Exception:
        is_sub = False

    sub_icon = "🔕" if is_sub else "🔔"
    sub_text = "Obunani bekor qilish" if is_sub else "Yangi qismlarga obuna bo'lish"

    caption = (
        f"🌌 <b>{name}</b> (Franshiza Xronologiyasi)\n\n"
        f"📚 Kinokoinotning barcha qismlarini to'liq voqealar ketma-ketligi bo'yicha tomosha qiling!\n\n"
        f"📝 <b>Tavsif:</b> {desc}\n\n"
        f"🔢 Jami qismlar: <b>{total} ta</b>\n"
        f"<i>Kerakli film ustiga bosib tomosha qilishingiz mumkin:</i>"
    )

    if len(caption) > 1000:
        caption = caption[:997] + "..."

    # Sort items by chronological order
    sorted_items = sorted(items, key=lambda x: x.get("chronological_order") or 0)
    buttons = []
    for idx, it in enumerate(sorted_items, 1):
        m = it.get("movie")
        s = it.get("series")
        if m:
            m_title = m.get("title", "")
            m_year = f" ({m.get('release_year')})" if m.get("release_year") else ""
            m_code = m.get("code")
            buttons.append([
                InlineKeyboardButton(
                    text=f"#{idx}-qism: {m_title}{m_year}",
                    callback_data=f"select_m_{m_code}"
                )
            ])
        elif s:
            s_title = s.get("title", "")
            s_year = f" ({s.get('release_year')})" if s.get("release_year") else ""
            buttons.append([
                InlineKeyboardButton(
                    text=f"#{idx}-qism: {s_title}{s_year}",
                    callback_data=f"search_series_{s.get('id')}"
                )
            ])

    if col_id:
        buttons.append([
            InlineKeyboardButton(
                text=f"{sub_icon} {sub_text}",
                callback_data=f"sub_col_{col_id}"
            )
        ])

    from config import settings
    base_site = getattr(settings, "WEBSITE_URL", "https://kinochi.uz").rstrip('/')
    slug = collection.get("slug") or col_id
    buttons.append([
        InlineKeyboardButton(text="🌐 Saytda to'liq ko'rish", url=f"{base_site}/collections/{slug}"),
        InlineKeyboardButton(text="❌ Yopish", callback_data="delete_msg")
    ])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

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
        print(f"Error sending collection info: {e}")
        return False
