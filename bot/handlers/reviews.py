import html
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from app.core.reviews import submit_review, get_reviews
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

@router.callback_query(F.data.startswith("reviews_m_"))
async def handle_view_movie_reviews(callback: CallbackQuery):
    code = callback.data.replace("reviews_m_", "")
    movie = await api_client.get_movie_by_code(code)
    if not movie:
        await callback.answer("Film topilmadi.", show_alert=True)
        return

    movie_id = movie.get("id")
    res = await get_reviews(movie_id=movie_id, limit=5)
    reviews_list = res.get("items", [])
    total = res.get("total", 0)
    avg_score = res.get("average_rating") or movie.get("kinochi_rating")
    imdb_score = movie.get("imdb_rating") or "N/A"

    title = html.escape(movie.get("title", "Film"))
    text = f"🎬 <b>{title}</b> — Fikrlar va Sharhlar\n\n"
    text += f"⭐ IMDb: <b>{imdb_score} / 10</b>\n"
    if avg_score:
        text += f"💜 Kinochi: <b>{avg_score} / 10</b> ({total} ta baho)\n\n"
    else:
        text += "💜 Kinochi: <i>Hozircha baholanmagan</i>\n\n"

    comments_with_text = [r for r in reviews_list if r.get("comment")]
    if comments_with_text:
        text += f"💬 <b>Foydalanuvchilar fikrlari ({len(comments_with_text)} ta):</b>\n\n"
        for r in comments_with_text[:5]:
            u_name = html.escape(r.get("user_name") or "Tomoshabin")
            c_text = html.escape(r.get("comment") or "")
            r_val = r.get("rating", 10)
            text += f"👤 <b>{u_name}</b> ({r_val} ⭐):\n«<i>{c_text}</i>»\n\n"
    else:
        text += "<i>Hozircha hech kim matnli fikr yozmagan. Birinchi bo'lib o'z fikringizni bildiring! 🍿</i>\n\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Baholash va Fikr qoldirish", callback_data=f"rate_m_{code}")],
        [InlineKeyboardButton(text="❌ Yopish", callback_data="delete_msg")]
    ])

    await callback.message.reply(text=text, parse_mode="HTML", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("reviews_s_"))
async def handle_view_series_reviews(callback: CallbackQuery):
    series_id_str = callback.data.replace("reviews_s_", "")
    try:
        series_id = int(series_id_str)
    except ValueError:
        await callback.answer("Xato ID.", show_alert=True)
        return

    series = await api_client.get_series_by_id(series_id)
    if not series:
        await callback.answer("Serial topilmadi.", show_alert=True)
        return

    res = await get_reviews(series_id=series_id, limit=5)
    reviews_list = res.get("items", [])
    total = res.get("total", 0)
    avg_score = res.get("average_rating") or series.get("kinochi_rating")
    imdb_score = series.get("imdb_rating") or "N/A"

    title = html.escape(series.get("title", "Serial"))
    text = f"📺 <b>{title}</b> — Fikrlar va Sharhlar\n\n"
    text += f"⭐ IMDb: <b>{imdb_score} / 10</b>\n"
    if avg_score:
        text += f"💜 Kinochi: <b>{avg_score} / 10</b> ({total} ta baho)\n\n"
    else:
        text += "💜 Kinochi: <i>Hozircha baholanmagan</i>\n\n"

    comments_with_text = [r for r in reviews_list if r.get("comment")]
    if comments_with_text:
        text += f"💬 <b>Foydalanuvchilar fikrlari ({len(comments_with_text)} ta):</b>\n\n"
        for r in comments_with_text[:5]:
            u_name = html.escape(r.get("user_name") or "Tomoshabin")
            c_text = html.escape(r.get("comment") or "")
            r_val = r.get("rating", 10)
            text += f"👤 <b>{u_name}</b> ({r_val} ⭐):\n«<i>{c_text}</i>»\n\n"
    else:
        text += "<i>Hozircha hech kim matnli fikr yozmagan. Birinchi bo'lib o'z fikringizni bildiring! 🍿</i>\n\n"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✍️ Baholash va Fikr qoldirish", callback_data=f"rate_s_{series_id}")],
        [InlineKeyboardButton(text="❌ Yopish", callback_data="delete_msg")]
    ])

    await callback.message.reply(text=text, parse_mode="HTML", reply_markup=kb)
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
