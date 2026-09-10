from aiogram import Router, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from app.core.watch_history import mark_movie_completed
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

    # Edit the button to "✅ Ko'rilgan" and disable it (remove callback_data or change it to something unhandled)
    old_markup = callback.message.reply_markup
    if old_markup:
        new_inline_keyboard = []
        for row in old_markup.inline_keyboard:
            new_row = []
            for btn in row:
                if btn.callback_data == callback.data:
                    # Replace with disabled-like button
                    from aiogram.types import InlineKeyboardButton
                    new_row.append(InlineKeyboardButton(text="✅ Ko'rilgan", callback_data="ignore_history"))
                else:
                    new_row.append(btn)
            new_inline_keyboard.append(new_row)
        
        new_markup = InlineKeyboardMarkup(inline_keyboard=new_inline_keyboard)
        await callback.message.edit_reply_markup(reply_markup=new_markup)
    
    await callback.answer("Film ko'rilganlar ro'yxatiga qo'shildi!")
    
@router.callback_query(F.data == "ignore_history")
async def handle_ignore_history(callback: CallbackQuery):
    await callback.answer("Siz bu filmni allaqachon ko'rib bo'lgansiz.")
