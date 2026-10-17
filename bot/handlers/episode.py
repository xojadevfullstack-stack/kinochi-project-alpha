from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.api_client import api_client
from utils.episode_sender import format_episode_caption, build_episode_keyboard
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(F.data.startswith("ep_prev:") | F.data.startswith("ep_next:"))
async def handle_episode_navigation(callback: CallbackQuery):
    try:
        code = callback.data.split(":", 1)[1]
        
        episode = await api_client.get_episode_by_code(code)
        if not episode:
            await callback.answer("⚠️ Qism topilmadi yoki o'chirilgan!", show_alert=True)
            return
            
        translations = episode.get("translations", [])
        if not translations:
            await callback.answer("⏳ Bu qism videosi hozircha yuklanmagan.", show_alert=True)
            return
            
        from utils.episode_sender import send_episode_to_user
        success = await send_episode_to_user(callback.bot, callback.from_user.id, episode)
        
        if success:
            try:
                await callback.message.delete()
            except Exception as e:
                logger.warning(f"Could not delete message in handle_episode_navigation: {e}")
        else:
            await callback.answer("Xatolik yuz berdi.", show_alert=True)
    finally:
        try:
            await callback.answer()
        except Exception:
            pass


@router.callback_query(F.data.startswith("series_info:"))
async def handle_series_info(callback: CallbackQuery):
    try:
        series_id = int(callback.data.split(":", 1)[1])
        
        series = await api_client.get_series_by_id(series_id)
        if not series:
            await callback.answer("⚠️ Serial ma'lumotlari topilmadi!", show_alert=True)
            return
            
        from utils.info_sender import send_series_info
        success = await send_series_info(callback.bot, callback.from_user.id, series)
        
        if success:
            try:
                await callback.message.delete()
            except Exception as e:
                logger.warning(f"Could not delete message in handle_series_info: {e}")
        else:
            await callback.answer("⚠️ Xatolik yuz berdi.", show_alert=True)
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

@router.callback_query(F.data.startswith("back_to_series:"))
async def handle_back_to_series(callback: CallbackQuery):
    try:
        series_id = int(callback.data.split(":", 1)[1])
        
        series = await api_client.get_series_by_id(series_id)
        if not series:
            await callback.answer("⚠️ Serial ma'lumotlari topilmadi!", show_alert=True)
            return
            
        from utils.info_sender import send_series_info
        success = await send_series_info(callback.bot, callback.from_user.id, series, edit_message_id=callback.message.message_id)
        
        if not success:
            await callback.answer("⚠️ Xatolik yuz berdi.", show_alert=True)
    finally:
        try:
            await callback.answer()
        except Exception:
            pass



