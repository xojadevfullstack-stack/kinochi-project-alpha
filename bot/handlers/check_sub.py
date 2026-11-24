import html
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from services.api_client import api_client
from middlewares.subscription_check import _extract_chat_targets, invalidate_user_sub_cache

router = Router()


@router.message(Command("subcheck"))
async def check_subscription_diag_command(message: Message):
    """Jonli Telegram kanal obuna tekshiruvi diagnostikasi (/subcheck)."""
    channels = await api_client.get_active_channels()
    if not channels:
        await message.answer("ℹ️ Backend'da faol majburiy obuna kanallari topilmadi (`[]`).")
        return

    lines = [f"📋 <b>Faol kanallar: {len(channels)} ta</b>"]
    me = await message.bot.get_me()
    for ch in channels:
        targets = _extract_chat_targets(ch)
        title = html.escape(str(ch.get("channel_title") or "Kanal"))
        lines.append(f"\n<b>#{ch.get('id')} — {title}</b> (targets: <code>{html.escape(str(targets))}</code>)")
        if not targets:
            lines.append("• ❌ Kanal username yoki ID yo'q")
            continue
        for t in targets:
            try:
                bot_m = await message.bot.get_chat_member(chat_id=t, user_id=me.id)
                usr_m = await message.bot.get_chat_member(chat_id=t, user_id=message.from_user.id)
                lines.append(
                    f"• <code>{html.escape(str(t))}</code>: bot=<b>{bot_m.status}</b>, siz=<b>{usr_m.status}</b>"
                )
                break
            except Exception as exc:
                lines.append(f"• <code>{html.escape(str(t))}</code>: ❌ <code>{html.escape(str(exc))}</code>")

    await message.answer("\n".join(lines), parse_mode="HTML")


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
