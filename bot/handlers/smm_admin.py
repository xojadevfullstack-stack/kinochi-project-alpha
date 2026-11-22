"""Telegram inline callback handlers for SMM Video Autopilot preview controls."""
import logging
import os

from aiogram import F, Router
from aiogram.types import CallbackQuery

from services.api_client import api_client

logger = logging.getLogger(__name__)
router = Router(name="smm_admin")

_ACTION_LABELS = {
    "smm_approve": "✅ Klipp tasdiqlandi va nashr navbatiga qo'shildi.",
    "smm_publish": "🚀 Klipp darhol kanalga chiqarish navbatiga yuborildi!",
    "smm_reject": "❌ Klipp rad etildi.",
}


def _is_smm_admin(user_id: int) -> bool:
    raw = ",".join(
        part
        for part in (os.getenv("SMM_ADMIN_TELEGRAM_ID", ""), os.getenv("ADMIN_IDS", ""))
        if part.strip()
    )
    allowed = {int(x.strip()) for x in raw.split(",") if x.strip().lstrip("-").isdigit()}
    return user_id in allowed


@router.callback_query(F.data.startswith(("smm_approve:", "smm_publish:", "smm_reject:")))
async def handle_smm_callback(callback: CallbackQuery) -> None:
    """Handle admin approve / publish now / reject inline buttons from SMM preview messages."""
    try:
        user_id = getattr(getattr(callback, "from_user", None), "id", 0)
        if not _is_smm_admin(int(user_id)):
            await callback.answer("⛔ Ruxsat yo'q: bu tugma faqat admin uchun.", show_alert=True)
            return

        raw_data = callback.data or ""
        prefix, _, raw_id = raw_data.partition(":")
        if not raw_id.isdigit():
            await callback.answer("Noto'g'ri SMM vazifa ID", show_alert=True)
            return

        job_id = int(raw_id)
        action = "reject" if prefix == "smm_reject" else "approve"
        publish_now = prefix == "smm_publish"

        result = await api_client.act_on_smm_job(job_id, action=action, publish_now=publish_now)
        if not result:
            await callback.answer("⚠️ Backend bilan bog'lanishda xato yuz berdi.", show_alert=True)
            return

        status_text = _ACTION_LABELS.get(prefix, "✅ Bajarildi")
        await callback.answer(status_text[:180], show_alert=False)
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        try:
            await callback.message.reply(f"{status_text}\n🔑 Vazifa ID: <code>#{job_id}</code>", parse_mode="HTML")
        except Exception:
            pass
    finally:
        try:
            await callback.answer()
        except Exception:
            pass
