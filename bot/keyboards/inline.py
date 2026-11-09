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
            col_id = item.get("id")
            builder.button(
                text=f"🌌 {title} (Xronologiya)",
                callback_data=f"col_view_{col_id}",
            )

    builder.adjust(1)
    return builder.as_markup()

from aiogram.types import WebAppInfo

def get_main_menu_inline(webapp_url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔍 Qidirish", switch_inline_query_current_chat="")
    builder.button(text="📂 Katalog", callback_data="menu_catalog")
    builder.button(text="🎲 Tavsiya", callback_data="menu_random")
    builder.button(text="👤 Profil", callback_data="menu_profile")
    
    # WebApp URL must be HTTPS for Telegram
    if not webapp_url or not webapp_url.startswith("https://"):
        webapp_url = "https://kinochi-project-alpha.vercel.app/"

    builder.button(text="🌐 Saytga o'tish", web_app=WebAppInfo(url=webapp_url))
    builder.adjust(1, 2, 2)
    return builder.as_markup()

def get_catalog_categories_inline(pages: list[dict] = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # 1. Asosiy bo'limlar: Kinolar va Seriallar
    builder.button(text="🎬 Kinolar", callback_data="catalog_all_movies")
    builder.button(text="📺 Seriallar", callback_data="catalog_all_series")
    
    # 2. Franshizalar & To'plamlar (alohida to'liq qator)
    builder.button(text="📚 Franshizalar & To'plamlar", callback_data="catalog_collections")
    
    # 3. Dinamik sahifalar (Admin panel va saytdan qo'shilgan, dublikatlar olib tashlanadi)
    dyn_count = 0
    if pages:
        for page in pages:
            if not page.get('is_active'):
                continue
            title = page.get('title', '').strip()
            slug = (page.get('slug') or '').strip().lower()
            t_lower = title.lower()

            # Dublikat kino va serial sahifalarini tashlab o'tish (chunki yuqorida 🎬 Kinolar va 📺 Seriallar mavjud)
            if slug in ("movie", "movies", "series", "serial", "film", "filmlar") or t_lower in ("kino", "kinolar", "serial", "seriallar", "film", "filmlar"):
                continue

            icon = "📂"
            if "anime" in t_lower:
                icon = "🥷"
            elif "dorama" in t_lower:
                icon = "🎭"
            elif "mult" in t_lower or "animatsiya" in t_lower:
                icon = "🧸"
            elif "premyera" in t_lower:
                icon = "🔥"
            elif "top" in t_lower:
                icon = "🏆"

            builder.button(text=f"{icon} {title}", callback_data=f"menu_page_{page.get('id')}")
            dyn_count += 1
                
    # 4. Asosiy menyu
    builder.button(text="🔙 Asosiy menyu", callback_data="menu_main")

    # Qatorlar kengligini ergonomik moslashtirish:
    # - [Kinolar, Seriallar] (2)
    # - [Franshizalar & To'plamlar] (1)
    # - Dinamik sahifalar 2 tadan (agar toq bo'lsa, oxirgisi 1)
    # - [Asosiy menyu] (1)
    adjust_pattern = [2, 1]
    for i in range(0, dyn_count, 2):
        if i + 1 < dyn_count:
            adjust_pattern.append(2)
        else:
            adjust_pattern.append(1)
    adjust_pattern.append(1)

    builder.adjust(*adjust_pattern)
    return builder.as_markup()

import math

def build_catalog_items_list(
    items: list[dict],
    item_type: str,
    page: int = 1,
    total: int = 0,
    page_size: int = 10
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1

    for item in items:
        title = item.get("title", "Noma'lum")
        year = item.get("release_year") or item.get("year")
        year_str = f" ({year})" if year else ""
        if item_type == "movie":
            builder.button(text=f"🎬 {title}{year_str}", callback_data=f"catalog_item_movie_{item.get('id')}")
        else:
            builder.button(text=f"📺 {title}{year_str}", callback_data=f"catalog_item_series_{item.get('id')}")
            
    builder.adjust(1)

    # Navigatsiya tugmalari (Pagination)
    if total_pages > 1:
        prefix = "cat_movies" if item_type == "movie" else "cat_series"
        pagination_row = []
        if page > 1:
            pagination_row.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"{prefix}:{page-1}"))
        else:
            pagination_row.append(InlineKeyboardButton(text="▪️", callback_data="cat_noop"))
            
        pagination_row.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data=f"cat_info:{page}:{total_pages}:{total}"))
        
        if page < total_pages:
            pagination_row.append(InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"{prefix}:{page+1}"))
        else:
            pagination_row.append(InlineKeyboardButton(text="▪️", callback_data="cat_noop"))
            
        builder.row(*pagination_row)

    builder.row(InlineKeyboardButton(text="🔙 Katalogga qaytish", callback_data="menu_catalog"))
    return builder.as_markup()

def build_page_items_list(
    items: list[dict],
    page_id: int,
    page: int = 1,
    total: int = 0,
    page_size: int = 10
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    total_pages = max(1, math.ceil(total / page_size)) if total > 0 else 1

    for item in items:
        title = item.get("title", "Noma'lum")
        year = item.get("release_year") or item.get("year")
        year_str = f" ({year})" if year else ""
        if item.get("type") == "movie":
            builder.button(text=f"🎬 {title}{year_str}", callback_data=f"catalog_item_movie_{item.get('id')}")
        elif item.get("type") == "series":
            builder.button(text=f"📺 {title}{year_str}", callback_data=f"catalog_item_series_{item.get('id')}")
            
    builder.adjust(1)

    # Navigatsiya tugmalari (Pagination)
    if total_pages > 1:
        pagination_row = []
        if page > 1:
            pagination_row.append(InlineKeyboardButton(text="◀️ Oldingi", callback_data=f"cat_dyn:{page_id}:{page-1}"))
        else:
            pagination_row.append(InlineKeyboardButton(text="▪️", callback_data="cat_noop"))
            
        pagination_row.append(InlineKeyboardButton(text=f"📄 {page}/{total_pages}", callback_data=f"cat_info:{page}:{total_pages}:{total}"))
        
        if page < total_pages:
            pagination_row.append(InlineKeyboardButton(text="Keyingi ▶️", callback_data=f"cat_dyn:{page_id}:{page+1}"))
        else:
            pagination_row.append(InlineKeyboardButton(text="▪️", callback_data="cat_noop"))
            
        builder.row(*pagination_row)

    builder.row(InlineKeyboardButton(text="🔙 Katalogga qaytish", callback_data="menu_catalog"))
    return builder.as_markup()
