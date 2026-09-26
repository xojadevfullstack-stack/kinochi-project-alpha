from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.api_client import api_client
from utils.info_sender import send_movie_info, send_series_info
from aiogram.exceptions import TelegramBadRequest
from config import settings
from keyboards.inline import get_main_menu_inline

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message, command: CommandObject):
    # Register or update user
    await api_client.register_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

    args = command.args
    if args and args.strip():
        raw_code = args.strip()
        
        # Check if it's login
        if raw_code.lower() == "login":
            return await cmd_login(message)
        
        from utils.code_resolver import resolve_and_send_content
        found = await resolve_and_send_content(message.bot, message.from_user.id, raw_code)
        if not found:
            await message.answer("❌ <b>Hech narsa topilmadi!</b>\n\nSiz yuborgan kod bo'yicha ma'lumot topilmadi. Kodni to'g'ri yozganingizga ishonch hosil qiling!", parse_mode="HTML")
        return
    else:
        welcome_text = (
            "👋 <b>MediaPlus botiga xush kelibsiz!</b>\n\n"
            "🎬 Eng sara kinolar va seriallar aynan shu yerda.\n"
            "🎥 Kinoni ko'rish uchun menyudan tanlang yoki izlang!\n\n"
            "🔍 <i>Qidirish uchun shunchaki kino nomini yozing.</i>"
        )
        
        webapp_url = getattr(settings, "WEBSITE_URL", "https://kinochi-project-alpha.vercel.app/").rstrip("/") + "/"
            
        await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu_inline(webapp_url))


@router.message(Command("login"))
async def cmd_login(message: Message):
    """Generates an instant 1-click magic login URL for the website."""
    try:
        await api_client.register_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
    except Exception as reg_err:
        import logging
        logging.getLogger(__name__).warning("register_user in cmd_login failed: %s", reg_err)

    try:
        token = await api_client.generate_login_token(
            telegram_id=message.from_user.id,
            first_name=message.from_user.first_name,
            username=message.from_user.username
        )
        
        # Ensure base_site is valid public HTTPS url (Telegram rejects localhost inline buttons)
        base_site = getattr(settings, "WEBSITE_URL", "https://kinochi-project-alpha.vercel.app").rstrip("/")
        if not base_site or "localhost" in base_site or "127.0.0.1" in base_site:
            base_site = "https://kinochi-project-alpha.vercel.app"

        if not token:
            await message.answer("❌ Profilga kirish havolasini tayyorlashda xatolik yuz berdi. Iltimos, birozdan so'ng qayta urinib ko'ring.")
            return

        login_url = f"{base_site}/?auth_token={token}"
        builder = InlineKeyboardBuilder()
        builder.button(text="🌐 Saytga kirish (Avtomatik)", url=login_url)
        await message.answer(
            "✅ <b>Saytga kirish tayyor!</b>\n\n"
            "Quyidagi tugmani bosing va darhol shaxsiy profilingizga kiring:",
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("cmd_login ichida xatolik yuz berdi: %s", e)
        await message.answer("Xatolik yuz berdi, iltimos qayta urinib ko'ring.")


