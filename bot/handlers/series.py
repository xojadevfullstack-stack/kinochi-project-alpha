from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.api_client import api_client
from utils.movie_sender import send_episode_to_user
from keyboards.inline import build_seasons_keyboard, build_episodes_keyboard

router = Router()

@router.callback_query(F.data.startswith("season_"))
async def handle_season_select(callback: CallbackQuery):
    season_id_str = callback.data.split("_")[1]
    if not season_id_str.isdigit():
        return
    season_id = int(season_id_str)
    
    episodes = await api_client.get_episodes(season_id)
    if not episodes:
        await callback.answer("Bu faslda qismlar yo'q", show_alert=True)
        return
        
    # We need the movie_id for the back button.
    # To avoid another API call if not strictly needed, we could put movie_id in callback data,
    # but currently we don't. Let's just do a quick get if necessary. 
    # Wait, get_episodes returns the episodes. Each episode has season_id, but not movie_id directly in the simple response unless we look it up.
    # Actually, getting seasons includes movie_id.
    # Let's just fetch all movies to find which one this season belongs to, or change the callback data in inline builder.
    # Let's change the inline builder in a bit, or just pass a dummy movie_id 0 and hide back button if not found.
    # Ah, the callback data for season was: `season_{s['id']}`.
    
    movie_id = 0
    # Actually, we can just get the movie_id from the first episode if it has it, or we just omit it for now
    # Let's edit inline.py to include movie_id in season callback: `season_{s['id']}_{movie_id}`
    # Wait, it's easier to just assume movie_id is available if we do that. Let's do that in inline.py soon.
    
    parts = callback.data.split("_")
    if len(parts) == 3:
        movie_id = int(parts[2])
    
    await callback.message.edit_reply_markup(reply_markup=build_episodes_keyboard(episodes, movie_id))
    await callback.answer()

@router.callback_query(F.data.startswith("episode_"))
async def handle_episode_select(callback: CallbackQuery):
    parts = callback.data.split("_")
    code = parts[1]
    movie_id = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0
    
    episode = await api_client.get_episode_by_code(code)
    if not episode:
        await callback.answer("Qism topilmadi", show_alert=True)
        return
        
    # Need to find prev and next codes for navigation
    episodes = await api_client.get_episodes(episode["season_id"])
    episodes.sort(key=lambda x: x["episode_number"])
    
    prev_code = None
    next_code = None
    
    for i, ep in enumerate(episodes):
        if ep["id"] == episode["id"]:
            if i > 0:
                prev_code = episodes[i-1]["code"]
            if i < len(episodes) - 1:
                next_code = episodes[i+1]["code"]
            break

    success = await send_episode_to_user(
        callback.bot, 
        callback.message.chat.id, 
        episode, 
        prev_code, 
        next_code,
        movie_id
    )
    if not success:
        await callback.answer("Kechirasiz, bu qism videosi hali yuklanmagan.", show_alert=True)
    else:
        await callback.answer()

@router.callback_query(F.data.startswith("back_to_seasons_"))
async def handle_back_to_seasons(callback: CallbackQuery):
    movie_id_str = callback.data.replace("back_to_seasons_", "")
    if not movie_id_str.isdigit():
        return
    movie_id = int(movie_id_str)
    
    seasons = await api_client.get_seasons(movie_id)
    if not seasons:
        await callback.answer("Fasllar topilmadi", show_alert=True)
        return
        
    await callback.message.edit_reply_markup(reply_markup=build_seasons_keyboard(seasons, movie_id))
    await callback.answer()
