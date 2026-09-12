import html
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.core.reviews import submit_review
from services.api_client import api_client

router = Router()

class ReviewStates(StatesGroup):
    waiting_for_comment = State()

def get_rating_keyboard(target_type: str, target_id: str | int) -> InlineKeyboardMarkup:
    """Creates a 1 to 10 star rating keyboard."""
    # Row 1: 1 to 5
    row1 = [
        InlineKeyboardButton(text=f"{i} ⭐", callback_data=f"setrate_{target_type}_{target_id}_{i}")
        for i in range(1, 6)
    ]
    # Row 2: 6 to 10
    row2 = [
        InlineKeyboardButton(text=f"{i} ⭐", callback_data=f"setrate_{target_type}_{target_id}_{i}")
        for i in range(6, 11)
    ]
    row3 = [
        InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_rate")
    ]
    return InlineKeyboardMarkup(inline_keyboard=[row1, row2, row3])

@router.callback_query(F.data.startswith("rate_m_"))
async def handle_rate_movie(callback: CallbackQuery):
    code = callback.data.replace("rate_m_", "")
    await callback.message.reply(
        "🎬 Ushbu filmni <b>1 dan 10 gacha</b> baholang:\n\n<i>1 ⭐ - Juda yomon\n10 ⭐ - A'lo darajada</i>",
        parse_mode="HTML",
        reply_markup=get_rating_keyboard("m", code)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("rate_s_"))
async def handle_rate_series(callback: CallbackQuery):
    series_id = callback.data.replace("rate_s_", "")
    await callback.message.reply(
        "📺 Ushbu serialni <b>1 dan 10 gacha</b> baholang:\n\n<i>1 ⭐ - Juda yomon\n10 ⭐ - A'lo darajada</i>",
        parse_mode="HTML",
        reply_markup=get_rating_keyboard("s", series_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("rate_ep_"))
async def handle_rate_episode(callback: CallbackQuery):
    ep_id = callback.data.replace("rate_ep_", "")
    await callback.message.reply(
        "🍿 Ushbu qismni <b>1 dan 10 gacha</b> baholang:\n\n<i>1 ⭐ - Juda yomon\n10 ⭐ - A'lo darajada</i>",
        parse_mode="HTML",
        reply_markup=get_rating_keyboard("ep", ep_id)
    )
    await callback.answer()

@router.callback_query(F.data.startswith("setrate_"))
async def handle_set_rating(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split("_")
    if len(parts) < 4:
        await callback.answer("Xato ma'lumot.")
        return

    target_type = parts[1]
    target_id = parts[2]
    score = int(parts[3])

    movie_id = None
    series_id = None
    episode_id = None

    if target_type == "m":
        if str(target_id).isdigit():
            movie_id = int(target_id)
        else:
            movie = await api_client.get_movie_by_code(str(target_id))
            if movie:
                movie_id = movie.get("id")
    elif target_type == "s":
        try:
            series_id = int(target_id)
        except ValueError:
            pass
    elif target_type == "ep":
        try:
            episode_id = int(target_id)
        except ValueError:
            pass

    res = await submit_review(
        user_id=callback.from_user.id,
        rating=score,
        movie_id=movie_id,
        series_id=series_id,
        episode_id=episode_id
    )

    kinochi_score = res.get("kinochi_rating")
    votes_count = res.get("kinochi_votes_count", 0)

    # Save state for optional comment
    await state.set_state(ReviewStates.waiting_for_comment)
    await state.update_data(
        target_type=target_type,
        target_id=target_id,
        movie_id=movie_id,
        series_id=series_id,
        episode_id=episode_id,
        rating=score
    )

    skip_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⏭ Fikr qoldirmaslik (O'tkazish)", callback_data="skip_comment")]
    ])

    text = f"🌟 <b>Sizning bahoingiz: {score}/10 qabul qilindi!</b>\n"
    if kinochi_score:
        text += f"💜 Yangi Kinochi reytingi: <b>{kinochi_score}/10</b> ({votes_count} ta ovoz)\n\n"
    text += (
        "✍️ <i>Ushbu kino/serial haqida o'z fikringiz (sharh) ni yozib yuborishingiz mumkin.\n"
        "Fikringiz saytda va botda boshqa foydalanuvchilarga ko'rinadi:</i>"
    )

    try:
        await callback.message.edit_text(text=text, parse_mode="HTML", reply_markup=skip_kb)
    except Exception:
        await callback.message.reply(text=text, parse_mode="HTML", reply_markup=skip_kb)

    await callback.answer()

@router.message(ReviewStates.waiting_for_comment)
async def handle_review_comment(message: Message, state: FSMContext):
    data = await state.get_data()
    comment_text = message.text

    if not comment_text or len(comment_text.strip()) < 2:
        await message.reply("Iltimos, sharhingizni matn ko'rinishida yozing yoki 'O'tkazish' tugmasini bosing.")
        return

    # Update review with comment
    await submit_review(
        user_id=message.from_user.id,
        rating=data.get("rating", 10),
        comment=comment_text[:1000],
        movie_id=data.get("movie_id"),
        series_id=data.get("series_id"),
        episode_id=data.get("episode_id")
    )

    await state.clear()
    await message.reply(
        "✅ <b>Fikringiz va bahoingiz muvaffaqiyatli saqlandi!</b>\n\n"
        "Sharhingiz uchun tashakkur, bu boshqa tomoshabinlar uchun juda foydali bo'ladi! 🍿",
        parse_mode="HTML"
    )

@router.callback_query(F.data == "skip_comment")
async def handle_skip_comment(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(
        "✅ <b>Bahoyingiz saqlandi!</b> Fikr bildirganingiz uchun rahmat! 🍿",
        parse_mode="HTML"
    )
    await callback.answer()

@router.callback_query(F.data == "cancel_rate")
async def handle_cancel_rate(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer("Bekor qilindi.")
