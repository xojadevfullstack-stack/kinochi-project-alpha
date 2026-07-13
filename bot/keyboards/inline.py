from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def build_movies_list_keyboard(movies: list[dict]) -> InlineKeyboardMarkup:
    """
    Builds an inline keyboard with a list of movies.
    Each button sends a callback data with the movie code.
    """
    builder = InlineKeyboardBuilder()
    
    for movie in movies:
        title = movie.get("title", "Kino")
        code = movie.get("code")
        
        builder.button(
            text=f"🎬 {title}",
            callback_data=f"movie_{code}"
        )
        
    builder.adjust(1) # One button per row
    return builder.as_markup()

def build_search_results_keyboard(results: list[dict]) -> InlineKeyboardMarkup:
    """
    Builds an inline keyboard for combined search results (movies and series).
    Each item must have a 'type' ('movie' or 'series').
    """
    builder = InlineKeyboardBuilder()
    
    for item in results:
        title = item.get("title", "Noma'lum")
        
        if item.get("type") == "movie":
            code = item.get("code")
            builder.button(
                text=f"🎬 {title}",
                callback_data=f"movie_{code}"
            )
        elif item.get("type") == "series":
            series_id = item.get("id")
            builder.button(
                text=f"📺 {title}",
                callback_data=f"search_series_{series_id}"
            )
            
    builder.adjust(1)
    return builder.as_markup()

from aiogram.types import WebAppInfo

def get_main_menu_inline(webapp_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Qidirish (Qanday?)", callback_data="help_search")
    builder.button(text="📂 Katalog", callback_data="menu_catalog")
    builder.button(text="🎲 Tavsiya", callback_data="menu_random")
    builder.button(text="🌐 Saytga o'tish", web_app=WebAppInfo(url=webapp_url))
    builder.adjust(1, 2, 1)
    return builder.as_markup()

def get_catalog_categories_inline() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🎬 Kinolar", callback_data="menu_movies")
    builder.button(text="📺 Seriallar", callback_data="menu_series")
    builder.button(text="🔙 Asosiy menyu", callback_data="menu_main")
    builder.adjust(2, 1)
    return builder.as_markup()

def build_catalog_items_list(items: list[dict], item_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        title = item.get("title", "Noma'lum")
        if item_type == "movie":
            builder.button(text=f"🎬 {title}", callback_data=f"catalog_item_movie_{item.get('id')}")
        else:
            builder.button(text=f"📺 {title}", callback_data=f"catalog_item_series_{item.get('id')}")
            
    builder.button(text="🔙 Katalogga qaytish", callback_data="menu_catalog")
    builder.adjust(1)
    return builder.as_markup()
