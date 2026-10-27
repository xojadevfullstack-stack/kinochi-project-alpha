from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.api_client import api_client
from utils.movie_sender import send_video_translation

router = Router()

@router.callback_query(F.data.startswith("tr_"))
async def process_translation_selection(callback: CallbackQuery):
    try:
        # data format: tr_M_{item_code}_{translation_id} or tr_E_{item_code}_{translation_id}
        parts = callback.data.split("_", 2)
        if len(parts) < 3:
            await callback.answer("Noma'lum xatolik.")
            return
            
        item_type = parts[1]
        rest = parts[2]
        if "_" not in rest:
            await callback.answer("Noma'lum xatolik.")
            return
        item_code, tr_id_str = rest.rsplit("_", 1)
        
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
            reply_markup = None
            item_id = movie.get("id")
            
        elif item_type == 'E':
            episode = await api_client.get_episode_by_code(item_code)
            if not episode:
                await callback.answer("Qism topilmadi.")
                return
                
            translations = episode.get("translations", [])
            from utils.episode_sender import format_episode_caption
            caption = format_episode_caption(episode)
            
            # Build episode keyboard for navigation
            from utils.episode_sender import build_episode_keyboard
            reply_markup = build_episode_keyboard(episode)
            item_id = episode.get("id")
        else:
            await callback.answer("Noma'lum tur.")
            return

        # Find the translation
        translation = next((t for t in translations if t["id"] == tr_id), None)
        
        if not translation:
            await callback.answer("Bu studiya videolari topilmadi.")
            return
        
        if item_type == 'M':
            caption = f"🍿 <b>{title}</b>\n\n{description}"
            
        await send_video_translation(callback.bot, callback.from_user.id, translation, caption, reply_markup=reply_markup, item_id=item_id, item_type=item_type)
    finally:
        try:
            await callback.answer()
        except Exception:
            pass
