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
                callback_data=f"series_{series_id}"
            )
            
    builder.adjust(1)
    return builder.as_markup()
