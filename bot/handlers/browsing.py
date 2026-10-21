from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from services.api_client import api_client
from utils.movie_sender import send_movie_to_user
from utils.episode_sender import send_episode_to_user
from utils.info_sender import send_movie_info, send_series_info, send_season_info
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(F.data.startswith("watch_m_") | (F.data.startswith("m_") & ~F.data.startswith("menu_")))
async def handle_watch_movie(callback: CallbackQuery):
    try:
        if callback.data.startswith("m_"):
            code = callback.data[2:].strip()
        else:
            code = callback.data.split("_", 2)[2].strip()
        movie = await api_client.get_movie_by_code(code)
        if not movie:
            await callback.message.answer("⚠️ Bu kino topilmadi.")
            return
            
        success = await send_movie_to_user(callback.bot, callback.from_user.id, movie)
        if not success:
            await callback.message.answer("⏳ Video yuklanmoqda...")
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

@router.callback_query(F.data.startswith("watch_e_") | F.data.startswith("ep_code_"))
async def handle_watch_episode(callback: CallbackQuery):
    try:
        if callback.data.startswith("ep_code_"):
            code = callback.data[8:].strip()
        else:
            code = callback.data.split("_", 2)[2].strip()
        episode = await api_client.get_episode_by_code(code)
        if not episode:
            await callback.message.answer("⚠️ Bu qism topilmadi.")
            return
            
        success = await send_episode_to_user(callback.bot, callback.from_user.id, episode)
        if not success:
            await callback.message.answer("⏳ Video yuklanmoqda...")
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

@router.callback_query(F.data.startswith("show_season_"))
async def handle_show_season(callback: CallbackQuery):
    try:
        parts = callback.data.split("_")
        series_id = int(parts[2])
        season_id = int(parts[3])
        
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
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

@router.callback_query(F.data == "delete_msg")
async def handle_delete_msg(callback: CallbackQuery):
    try:
        try:
            await callback.message.delete()
        except Exception as e:
            logger.warning(f"Could not delete message in handle_delete_msg: {e}")
    finally:
        try:
            await callback.answer()
        except Exception:
            pass



@router.callback_query(F.data.startswith("franchise_m_"))
async def handle_movie_franchise(callback: CallbackQuery):
    try:
        code = callback.data.split("_", 2)[2]
        franchise = await api_client.get_movie_franchise_context(code)
        if not franchise or not franchise.get("timeline_items"):
            await callback.answer("Boshqa qismlar mavjud emas", show_alert=True)
            return

        items = franchise.get("timeline_items", [])
        buttons = []
        for it in items:
            m = it.get("movie")
            if not m:
                continue
            m_code = m.get("code")
            m_title = m.get("title", "")
            order = it.get("chronological_order") or 1
            year = m.get("release_year")
            is_current = bool(m_code and m_code.upper() == code.upper())

            label = f"#{order}-qism: {m_title}"
            if year:
                label += f" ({year})"

            if is_current:
                label = f"• {label} (Hozirgi)"
                buttons.append([InlineKeyboardButton(text=label, callback_data=f"noop_curr_{m_code}")])
            else:
                buttons.append([InlineKeyboardButton(text=label, callback_data=f"select_m_{m_code}")])

        buttons.append([InlineKeyboardButton(text="Ortga", callback_data=f"select_m_{code}")])

        kb = InlineKeyboardMarkup(inline_keyboard=buttons)
        try:
            await callback.message.edit_reply_markup(reply_markup=kb)
        except Exception as e:
            logger.warning(f"Failed to edit markup in handle_movie_franchise: {e}")
    finally:
        try:
            await callback.answer()
        except Exception:
            pass


@router.callback_query(F.data.startswith("select_m_"))
async def handle_select_movie(callback: CallbackQuery):
    try:
        code = callback.data.split("_", 2)[2]
        movie = await api_client.get_movie_by_code(code)
        if not movie:
            await callback.answer("Kino topilmadi", show_alert=True)
            return

        await send_movie_info(
            callback.bot,
            callback.from_user.id,
            movie,
            edit_message_id=callback.message.message_id,
        )
    finally:
        try:
            await callback.answer()
        except Exception:
            pass


@router.callback_query(F.data.startswith("noop_curr_"))
async def handle_noop_current(callback: CallbackQuery):
    try:
        await callback.answer("Siz hozir shu qismdasiz", show_alert=False)
    finally:
        try:
            await callback.answer()
        except Exception:
            pass
