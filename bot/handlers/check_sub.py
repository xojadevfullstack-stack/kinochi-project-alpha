from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.api_client import api_client
from middlewares.subscription_check import invalidate_user_sub_cache

router = Router()

@router.callback_query(F.data == "check_subscription")
async def check_subscription_callback(callback: CallbackQuery):
    try:
        user_id = callback.from_user.id
        invalidate_user_sub_cache(user_id)
        # Agar middleware'dan o'tib bu yerga kelsa, barcha kanallarga obuna bo'lgan.
        channels = await api_client.get_active_channels()
        
        for ch in channels:
            await api_client.verify_channel_subscription(ch['id'], user_id)
            
        await callback.message.delete()
        await callback.message.answer("Rahmat! Obunangiz tasdiqlandi. Endi /start orqali botdan foydalanishingiz mumkin.")
    finally:
        try:
            await callback.answer()
        except Exception:
            pass
