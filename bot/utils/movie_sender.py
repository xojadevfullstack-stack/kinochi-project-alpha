from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from config import settings

async def send_movie_to_user(bot: Bot, chat_id: int, movie: dict) -> bool:
    """
    Sends a movie video to the specified chat_id.
    Attempts to send via telegram_file_id first, then falls back to copying
    from the storage channel if available.
    
    Returns True if successfully sent, False otherwise.
    """
    is_series = movie.get("is_series", False)
    
    # If it is a series, we don't send a video immediately.
    # We send the poster and the list of seasons.
    if is_series:
        from keyboards.inline import build_seasons_keyboard
        from services.api_client import api_client
        seasons = await api_client.get_seasons(movie["id"])
        
        caption = f"🍿 <b>{movie.get('title')}</b> (Serial)\n\n{movie.get('description') or ''}\n\nFaslni tanlang:"
        
        # In a real app we'd fetch the poster and send_photo if available.
        # But we can just send a text message for now to keep it simple and consistent.
        # Wait, if we have poster, we can send it.
        poster = movie.get("poster_url")
        if poster:
            try:
                await bot.send_photo(chat_id=chat_id, photo=poster, caption=caption, parse_mode="HTML", reply_markup=build_seasons_keyboard(seasons, movie["id"]))
                return True
            except TelegramBadRequest:
                pass
        
        await bot.send_message(chat_id=chat_id, text=caption, parse_mode="HTML", reply_markup=build_seasons_keyboard(seasons, movie["id"]))
        return True

    # Otherwise it is a single movie.
    file_id = movie.get("telegram_file_id")
    storage_msg_id = movie.get("storage_channel_message_id")
    caption = f"🍿 <b>{movie.get('title')}</b>\n\n{movie.get('description') or ''}"

    success = False
    
    # 1. Try sending via telegram_file_id
    if file_id:
        try:
            await bot.send_video(chat_id=chat_id, video=file_id, caption=caption, parse_mode="HTML")
            success = True
        except TelegramBadRequest:
            pass
            
    # 2. Fallback to copy from storage channel
    if not success and storage_msg_id and hasattr(settings, 'STORAGE_CHANNEL_ID') and settings.STORAGE_CHANNEL_ID:
        try:
            await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=settings.STORAGE_CHANNEL_ID,
                message_id=storage_msg_id,
                caption=caption,
                parse_mode="HTML"
            )
            success = True
        except TelegramBadRequest:
            pass

    return success

async def send_episode_to_user(bot: Bot, chat_id: int, episode: dict, prev_code: str | None, next_code: str | None, movie_id: int = 0) -> bool:
    from keyboards.inline import build_episode_nav_keyboard
    
    file_id = episode.get("telegram_file_id")
    storage_msg_id = episode.get("storage_channel_message_id")
    title_text = f" - {episode['title']}" if episode.get('title') else ""
    caption = f"📺 <b>{episode['episode_number']}-Qism</b>{title_text}\n(Kod: {episode['code']})"

    markup = build_episode_nav_keyboard(prev_code, next_code, episode["season_id"], movie_id)
    success = False
    
    if file_id:
        try:
            await bot.send_video(chat_id=chat_id, video=file_id, caption=caption, parse_mode="HTML", reply_markup=markup)
            success = True
        except TelegramBadRequest:
            pass
            
    if not success and storage_msg_id and hasattr(settings, 'STORAGE_CHANNEL_ID') and settings.STORAGE_CHANNEL_ID:
        try:
            await bot.copy_message(
                chat_id=chat_id,
                from_chat_id=settings.STORAGE_CHANNEL_ID,
                message_id=storage_msg_id,
                caption=caption,
                parse_mode="HTML",
                reply_markup=markup
            )
            success = True
        except TelegramBadRequest:
            pass

    return success
