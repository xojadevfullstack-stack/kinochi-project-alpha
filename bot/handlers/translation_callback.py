from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.api_client import api_client
from utils.movie_sender import send_video_translation

router = Router()

@router.callback_query(F.data.startswith("tr_"))
async def process_translation_selection(callback: CallbackQuery):
    # data format: tr_M_{item_id}_{translation_id} or tr_E_{item_id}_{translation_id}
    parts = callback.data.split("_")
    if len(parts) != 4:
        await callback.answer("Noma'lum xatolik.")
        return
        
    _, item_type, item_code, tr_id_str = parts
    
    try:
        tr_id = int(tr_id_str)
    except ValueError:
        await callback.answer("Noto'g'ri ma'lumot.")
        return
        
    # Fetch the movie or episode to get the translations
    if item_type == 'M':
        movie = await api_client.get_movie_by_code(item_code)
        if not movie:
            await callback.answer("Kino topilmadi.")
            return
            
        translations = movie.get("translations", [])
        title = movie.get("title", "")
        description = movie.get("description", "")
        
    elif item_type == 'E':
        episode = await api_client.get_episode_by_code(item_code)
        if not episode:
            await callback.answer("Qism topilmadi.")
            return
            
        translations = episode.get("translations", [])
        title = episode.get("title", f"{episode.get('episode_number')}-qism")
        description = ""
    else:
        await callback.answer("Noma'lum tur.")
        return

    # Find the translation
    translation = next((t for t in translations if t["id"] == tr_id), None)
    
    if not translation:
        await callback.answer("Bu studiya videolari topilmadi.")
        return
        
    await callback.answer()
    
    caption = f"🍿 <b>{title}</b>\n\n{description}"
    await send_video_translation(callback.bot, callback.from_user.id, translation, caption)
