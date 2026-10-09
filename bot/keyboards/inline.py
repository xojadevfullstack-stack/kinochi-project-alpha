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
    Builds an inline keyboard for live search results (movies, series, and collections).
    """
    from config import settings
    builder = InlineKeyboardBuilder()

    for item in results:
        title = item.get("title", "Noma'lum")
        year = item.get("year")
        rating = item.get("imdb_rating")
        year_str = f" ({year})" if year else ""
        rating_str = f" ⭐ {rating:.1f}" if rating else ""

        item_type = item.get("type")
        if item_type == "movie":
            code = item.get("code")
            builder.button(
                text=f"🎬 {title}{year_str}{rating_str}",
                callback_data=f"movie_{code}",
            )
        elif item_type == "series":
            series_id = item.get("id")
            builder.button(
                text=f"📺 {title}{year_str}{rating_str}",
                callback_data=f"search_series_{series_id}",
            )
        elif item_type == "collection":
            slug = item.get("code") or item.get("slug")
            web_url = f"{settings.WEBSITE_URL.rstrip('/')}/collections/{slug}"
            builder.button(
                text=f"🌌 {title} (Xronologiya)",
                url=web_url,
            )

    builder.adjust(1)
    return builder.as_markup()

from aiogram.types import WebAppInfo

def get_main_menu_inline(webapp_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Qidirish (Qanday?)", callback_data="help_search")
    builder.button(text="📂 Katalog", callback_data="menu_catalog")
    builder.button(text="🎲 Tavsiya", callback_data="menu_random")
    
    # WebApp URL must be HTTPS for Telegram
    if not webapp_url or not webapp_url.startswith("https://"):
        webapp_url = "https://kinochi-project-alpha.vercel.app/"

    builder.button(text="🌐 Saytga o'tish", web_app=WebAppInfo(url=webapp_url))
    builder.adjust(1, 2, 1)
    return builder.as_markup()

def get_catalog_categories_inline(pages: list[dict] = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Asosiy bo'limlar
    builder.button(text="🎬 Kinolar", callback_data="catalog_all_movies")
    builder.button(text="📺 Seriallar", callback_data="catalog_all_series")
    
    # Dinamik sahifalar (Admin panel va saytdan qo'shilgan)
    if pages:
        for page in pages:
            if page.get('is_active'):
                title = page.get('title', '')
                icon = "📂"
                t_lower = title.lower()
                if "anime" in t_lower:
                    icon = "🎌"
                elif "dorama" in t_lower:
                    icon = "🎭"
                elif "mult" in t_lower:
                    icon = "🧸"
                builder.button(text=f"{icon} {title}", callback_data=f"menu_page_{page.get('id')}")
                
    builder.button(text="🔙 Asosiy menyu", callback_data="menu_main")
    builder.adjust(2)
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

def build_page_items_list(items: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for item in items:
        title = item.get("title", "Noma'lum")
        if item.get("type") == "movie":
            builder.button(text=f"🎬 {title}", callback_data=f"catalog_item_movie_{item.get('id')}")
        elif item.get("type") == "series":
            builder.button(text=f"📺 {title}", callback_data=f"catalog_item_series_{item.get('id')}")
            
    builder.button(text="🔙 Katalogga qaytish", callback_data="menu_catalog")
    builder.adjust(1)
    return builder.as_markup()
