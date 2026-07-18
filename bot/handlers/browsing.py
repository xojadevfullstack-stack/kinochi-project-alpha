from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.api_client import api_client
from utils.movie_sender import send_movie_to_user
from utils.episode_sender import send_episode_to_user
from utils.info_sender import send_series_info, send_season_info
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(F.data.startswith("watch_m_"))
async def handle_watch_movie(callback: CallbackQuery):
    code = callback.data.split("_", 2)[2]
    await callback.answer()
    
    movie = await api_client.get_movie_by_code(code)
    if not movie:
        await callback.message.answer("⚠️ Bu kino topilmadi.")
        return
        
    success = await send_movie_to_user(callback.bot, callback.from_user.id, movie)
    if not success:
        await callback.message.answer("⏳ Video yuklanmoqda...")

@router.callback_query(F.data.startswith("watch_e_"))
async def handle_watch_episode(callback: CallbackQuery):
    code = callback.data.split("_", 2)[2]
    await callback.answer()
    
    episode = await api_client.get_episode_by_code(code)
    if not episode:
        await callback.message.answer("⚠️ Bu qism topilmadi.")
        return
        
    success = await send_episode_to_user(callback.bot, callback.from_user.id, episode)
    if not success:
        await callback.message.answer("⏳ Video yuklanmoqda...")

@router.callback_query(F.data.startswith("show_season_"))
async def handle_show_season(callback: CallbackQuery):
    parts = callback.data.split("_")
    series_id = int(parts[2])
    season_id = int(parts[3])
    
    await callback.answer()
    
    series = await api_client.get_series_by_id(series_id)
    if not series:
        await callback.message.answer("⚠️ Bu serial topilmadi.")
        return
        
    seasons = series.get("seasons", [])
    target_season = next((s for s in seasons if s.get("id") == season_id), None)
    
    if not target_season:
        await callback.message.answer("⚠️ Bu fasl topilmadi.")
        return
        
    target_season["series_id"] = series_id # Inject series_id for the back button
    
    # We can delete the old series message and send the new one, or edit media.
    # Because going from Series Poster to Season Poster involves editing media, let's just use send_season_info which handles editing if we pass edit_message_id.
    success = await send_season_info(callback.bot, callback.from_user.id, target_season, edit_message_id=callback.message.message_id, series_poster=series.get("poster_url"))
    if not success:
        await callback.message.answer("Xatolik yuz berdi.")

@router.callback_query(F.data == "delete_msg")
async def handle_delete_msg(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Could not delete message in handle_delete_msg: {e}")
    await callback.answer()
