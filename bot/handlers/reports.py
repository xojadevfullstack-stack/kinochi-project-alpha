import logging
import html
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.api_client import api_client

logger = logging.getLogger(__name__)

router = Router()

ISSUE_OPTIONS = [
    ("🖼 Poster / nom noto'g'ri", "poster_xato"),
    ("🎞 Video ochilmayapti / xato", "video_xato"),
    ("🔇 Ovoz / tarjima sifatsiz", "ovoz_xato"),
    ("🍿 Treyler ishlamayapti", "treyler_xato"),
    ("👥 Dublikat material", "dublikat"),
    ("✍️ Boshqa kamchilik", "boshqa"),
]


@router.callback_query(F.data.startswith("report_m_"))
async def handle_movie_report_prompt(callback: CallbackQuery):
    code = callback.data.replace("report_m_", "").strip()
    
    text = (
        "⚠️ <b>Film bo'yicha xatolikni bildirish</b>\n\n"
        "Qanday muammo yoki kamchilikka duch keldingiz? Quyidagi toifalardan birini tanlang:"
    )
    builder = InlineKeyboardBuilder()
    for label, itype in ISSUE_OPTIONS:
        builder.button(text=label, callback_data=f"rep_do:m:{code}:{itype}")
    builder.button(text="❌ Bekor qilish", callback_data="rep_cancel")
    builder.adjust(1)

    await callback.message.reply(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("report_s_"))
async def handle_series_report_prompt(callback: CallbackQuery):
    series_id = callback.data.replace("report_s_", "").strip()
    
    text = (
        "⚠️ <b>Serial bo'yicha nosozlikni bildirish</b>\n\n"
        "Qanday muammo yoki kamchilikka duch keldingiz? Quyidagi toifalardan birini tanlang:"
    )
    builder = InlineKeyboardBuilder()
    for label, itype in ISSUE_OPTIONS:
        builder.button(text=label, callback_data=f"rep_do:s:{series_id}:{itype}")
    builder.button(text="❌ Bekor qilish", callback_data="rep_cancel")
    builder.adjust(1)

    await callback.message.reply(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("report_e_"))
async def handle_episode_report_prompt(callback: CallbackQuery):
    ep_id = callback.data.replace("report_e_", "").strip()
    
    text = (
        "⚠️ <b>Qism bo'yicha nosozlikni bildirish</b>\n\n"
        "Qanday muammo yoki kamchilikka duch keldingiz? Quyidagi toifalardan birini tanlang:"
    )
    builder = InlineKeyboardBuilder()
    for label, itype in ISSUE_OPTIONS:
        builder.button(text=label, callback_data=f"rep_do:e:{ep_id}:{itype}")
    builder.button(text="❌ Bekor qilish", callback_data="rep_cancel")
    builder.adjust(1)

    await callback.message.reply(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("rep_do:"))
async def handle_execute_report(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer("Noto'g'ri so'rov formati.")
        return

    _, m_type, code_or_id, issue_type = parts

    movie_id = None
    series_id = None
    episode_id = None

    if m_type == "m":
        movie = await api_client.get_movie_by_code(code_or_id)
        if movie:
            movie_id = movie.get("id")
        elif code_or_id.isdigit():
            movie_id = int(code_or_id)
        media_type = "movie"
    elif m_type == "e":
        if code_or_id.isdigit():
            episode_id = int(code_or_id)
        else:
            ep = await api_client.get_episode_by_code(code_or_id)
            if ep:
                episode_id = ep.get("id")
                series_id = ep.get("series_id")
        media_type = "episode"
    else:
        if code_or_id.isdigit():
            series_id = int(code_or_id)
        media_type = "series"

    user_info = f"Telegram ID: {callback.from_user.id}"
    if callback.from_user.username:
        user_info += f" (@{callback.from_user.username})"

    desc = f"Telegram bot foydalanuvchisi ({user_info}) tomonidan xabar qilindi."
    success = await api_client.submit_report(
        media_type=media_type,
        issue_type=issue_type,
        movie_id=movie_id,
        series_id=series_id,
        episode_id=episode_id,
        description=desc
    )

    if success:
        await callback.answer("✅ Rahmat! Nosozlik haqida adminlarga xabar berildi.", show_alert=True)
        try:
            await callback.message.edit_text(
                "✅ <b>Nosozlik haqida xabar qabul qilindi!</b>\n\n"
                "Ko'rsatgan yordamingiz uchun rahmat. Tez orada adminlarimiz kamchilikni ko'rib chiqishadi.",
                parse_mode="HTML"
            )
        except Exception:
            pass
    else:
        await callback.answer("⚠️ Xabarni yuborishda xatolik yuz berdi. Iltimos birozdan so'ng urinib ko'ring.", show_alert=True)


@router.callback_query(F.data == "rep_cancel")
async def handle_cancel_report(callback: CallbackQuery):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer("Bekor qilindi.")
