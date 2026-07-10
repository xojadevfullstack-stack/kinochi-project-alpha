from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()

@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery):
    # Agar middleware'dan o'tib bu yerga kelsa, barcha kanallarga obuna bo'lgan.
    await callback.message.delete()
    await callback.message.answer("Rahmat! Obunangiz tasdiqlandi. Endi /start orqali botdan foydalanishingiz mumkin.")
    await callback.answer()
