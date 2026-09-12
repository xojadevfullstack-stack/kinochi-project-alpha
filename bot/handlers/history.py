from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from app.core.watch_history import mark_movie_completed, mark_episode_completed, mark_series_completed
from utils.movie_sender import notify_achievements

router = Router()

@router.callback_query(F.data.startswith("history_complete_movie_"))
async def handle_complete_movie(callback: CallbackQuery):
    movie_id_str = callback.data.replace("history_complete_movie_", "")
    try:
        movie_id = int(movie_id_str)
    except ValueError:
        await callback.answer("Xato ID.")
        return

    # Mark as completed in DB
    unlocked = await mark_movie_completed(callback.from_user.id, movie_id)
    if unlocked:
        await notify_achievements(callback.bot, callback.from_user.id, unlocked)

    # Edit the button to "✅ Ko'rilgan" and disable it
    old_markup = callback.message.reply_markup
    if old_markup:
        new_inline_keyboard = []
        for row in old_markup.inline_keyboard:
            new_row = []
            for btn in row:
                if btn.callback_data == callback.data:
                    new_row.append(InlineKeyboardButton(text="✅ Ko'rilgan", callback_data="ignore_history"))
                else:
                    new_row.append(btn)
            new_inline_keyboard.append(new_row)
        
        new_markup = InlineKeyboardMarkup(inline_keyboard=new_inline_keyboard)
        await callback.message.edit_reply_markup(reply_markup=new_markup)
    
    await callback.answer("Film ko'rilganlar ro'yxatiga qo'shildi!")

    try:
        from handlers.reviews import get_rating_keyboard
        await callback.message.reply(
            "🎬 <b>Film sizga yoqdimi?</b>\nUni 1 dan 10 gacha baholang va fikringizni bildiring:",
            parse_mode="HTML",
            reply_markup=get_rating_keyboard("m", movie_id)
        )
    except Exception:
        pass

@router.callback_query(F.data.startswith("history_complete_ep_"))
async def handle_complete_episode(callback: CallbackQuery):
    ep_id_str = callback.data.replace("history_complete_ep_", "")
    try:
        episode_id = int(ep_id_str)
    except ValueError:
        await callback.answer("Xato ID.")
        return

    # Mark episode as completed in DB
    unlocked = await mark_episode_completed(callback.from_user.id, episode_id)
    if unlocked:
        await notify_achievements(callback.bot, callback.from_user.id, unlocked)

    # Edit the button to "✅ Ko'rilgan"
    old_markup = callback.message.reply_markup
    if old_markup:
        new_inline_keyboard = []
        for row in old_markup.inline_keyboard:
            new_row = []
            for btn in row:
                if btn.callback_data == callback.data:
                    new_row.append(InlineKeyboardButton(text="✅ Ko'rilgan", callback_data="ignore_history"))
                else:
                    new_row.append(btn)
            new_inline_keyboard.append(new_row)
        
        new_markup = InlineKeyboardMarkup(inline_keyboard=new_inline_keyboard)
        try:
            await callback.message.edit_reply_markup(reply_markup=new_markup)
        except Exception:
            pass

    await callback.answer("Qism ko'rilganlar ro'yxatiga qo'shildi!")

    try:
        from handlers.reviews import get_rating_keyboard
        await callback.message.reply(
            "🍿 <b>Ushbu qism sizga yoqdimi?</b>\nUni 1 dan 10 gacha baholang va fikringizni bildiring:",
            parse_mode="HTML",
            reply_markup=get_rating_keyboard("ep", episode_id)
        )
    except Exception:
        pass

@router.callback_query(F.data.startswith("history_complete_series_"))
async def handle_complete_series(callback: CallbackQuery):
    series_id_str = callback.data.replace("history_complete_series_", "")
    try:
        series_id = int(series_id_str)
    except ValueError:
        await callback.answer("Xato ID.")
        return

    success, message, unlocked = await mark_series_completed(callback.from_user.id, series_id)

    if success:
        if unlocked:
            await notify_achievements(callback.bot, callback.from_user.id, unlocked)

        # Edit the button to "✅ To'liq ko'rilgan"
        old_markup = callback.message.reply_markup
        if old_markup:
            new_inline_keyboard = []
            for row in old_markup.inline_keyboard:
                new_row = []
                for btn in row:
                    if btn.callback_data == callback.data:
                        new_row.append(InlineKeyboardButton(text="✅ To'liq ko'rilgan", callback_data="ignore_history"))
                    else:
                        new_row.append(btn)
                new_inline_keyboard.append(new_row)

            new_markup = InlineKeyboardMarkup(inline_keyboard=new_inline_keyboard)
            try:
                await callback.message.edit_reply_markup(reply_markup=new_markup)
            except Exception:
                pass

        try:
            from handlers.reviews import get_rating_keyboard
            await callback.message.reply(
                "📺 <b>Serial sizga yoqdimi?</b>\nUni 1 dan 10 gacha baholang va fikringizni bildiring:",
                parse_mode="HTML",
                reply_markup=get_rating_keyboard("s", series_id)
            )
        except Exception:
            pass

    await callback.answer(message, show_alert=True)

@router.callback_query(F.data == "ignore_history")
async def handle_ignore_history(callback: CallbackQuery):
    await callback.answer("Siz buni allaqachon to'liq ko'rib bo'lgansiz.")


