from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.api_client import api_client
from utils.episode_sender import format_episode_caption, build_episode_keyboard

router = Router()

@router.callback_query(F.data.startswith("ep_prev:") | F.data.startswith("ep_next:"))
async def handle_episode_navigation(callback: CallbackQuery):
    code = callback.data.split(":", 1)[1]
    
    episode = await api_client.get_episode_by_code(code)
    if not episode:
        await callback.answer("⚠️ Qism topilmadi yoki o'chirilgan!", show_alert=True)
        return
        
    file_id = episode.get("telegram_file_id")
    if not file_id:
        await callback.answer("⏳ Bu qism videosi hozircha yuklanmagan.", show_alert=True)
        return
        
    caption = format_episode_caption(episode)
    keyboard = build_episode_keyboard(episode)
    
    try:
        from aiogram.types import InputMediaVideo
        media = InputMediaVideo(media=file_id, caption=caption, parse_mode="HTML")
        await callback.message.edit_media(media=media, reply_markup=keyboard)
        await callback.answer()
    except Exception as e:
        # If the message is the same or any other error
        await callback.answer("Xatolik yuz berdi yoki video o'zgarmadi.", show_alert=False)


@router.callback_query(F.data.startswith("series_info:"))
async def handle_series_info(callback: CallbackQuery):
    series_id = int(callback.data.split(":", 1)[1])
    
    series = await api_client.get_series_by_id(series_id)
    if not series:
        await callback.answer("⚠️ Serial ma'lumotlari topilmadi!", show_alert=True)
        return
        
    title = series.get("title", "")
    seasons = series.get("seasons", [])
    
    total_episodes = sum(len(s.get("episodes", [])) for s in seasons)
    
    text = f"🎬 <b>{title}</b>\n\n"
    text += f"📊 <b>Umumiy qismlar:</b> {total_episodes} ta\n\n"
    
    if seasons:
        text += "📚 <b>Mavsumlar:</b>\n"
        for s in sorted(seasons, key=lambda x: x.get("season_number", 0)):
            s_num = s.get("season_number")
            s_desc = s.get("description") or "Ma'lumot yo'q"
            ep_count = len(s.get("episodes", []))
            text += f"\n🔹 <b>{s_num}-mavsum</b> ({ep_count} ta qism)\n<i>{s_desc}</i>\n"
    else:
        text += "Hali mavsumlar qo'shilmagan."
        
    await callback.answer()
    await callback.message.answer(text, parse_mode="HTML")


@router.callback_query(F.data == "main_menu")
async def handle_main_menu_callback(callback: CallbackQuery):
    await callback.answer()
    from keyboards.reply import main_menu
    welcome_text = (
        "👋 <b>Kinochi botiga xush kelibsiz!</b>\n\n"
        "🎬 Eng sara kinolar va seriallar aynan shu yerda.\n"
        "🎥 Kinoni ko'rish uchun <b>kino kodini</b> yuboring yoki saytimiz orqali tanlang!\n\n"
        "🔍 <i>Qidirish uchun shunchaki kino nomini yozing.</i>"
    )
    await callback.message.answer(welcome_text, parse_mode="HTML", reply_markup=main_menu)
