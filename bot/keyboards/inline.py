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

def build_seasons_keyboard(seasons: list[dict], movie_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in seasons:
        builder.button(
            text=f"🎬 {s['season_number']}-Fasl",
            callback_data=f"season_{s['id']}_{movie_id}"
        )
    builder.adjust(2)
    return builder.as_markup()

def build_episodes_keyboard(episodes: list[dict], movie_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for ep in episodes:
        builder.button(
            text=f"{ep['episode_number']}-Qism",
            callback_data=f"episode_{ep['code']}_{movie_id}"
        )
    builder.adjust(4)
    builder.row(InlineKeyboardButton(text="🔙 Orqaga (Fasllar)", callback_data=f"back_to_seasons_{movie_id}"))
    return builder.as_markup()

def build_episode_nav_keyboard(prev_code: str | None, next_code: str | None, season_id: int, movie_id: int = 0) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    nav_buttons = []
    if prev_code:
        nav_buttons.append(InlineKeyboardButton(text="⏪ Oldingi qism", callback_data=f"episode_{prev_code}_{movie_id}"))
    if next_code:
        nav_buttons.append(InlineKeyboardButton(text="Keyingi qism ⏩", callback_data=f"episode_{next_code}_{movie_id}"))
    
    if nav_buttons:
        builder.row(*nav_buttons)
        
    builder.row(InlineKeyboardButton(text="🔙 Qismlar ro'yxati", callback_data=f"season_{season_id}_{movie_id}"))
    return builder.as_markup()
