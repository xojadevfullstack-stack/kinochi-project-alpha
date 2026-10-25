import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject, Command
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.api_client import api_client
from utils.info_sender import send_movie_info, send_series_info
from aiogram.exceptions import TelegramBadRequest
from config import settings
from keyboards.inline import get_main_menu_inline

logger = logging.getLogger(__name__)

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

        # Check if it's series subscription from web
        if raw_code.startswith("sub_series_"):
            try:
                series_id = int(raw_code.replace("sub_series_", ""))
                is_sub = await api_client.check_series_subscription(series_id, message.from_user.id)
                if not is_sub:
                    await api_client.toggle_series_subscription(series_id, message.from_user.id)
                series = await api_client.get_series_by_id(series_id)
                s_title = series.get("title", "Serial") if series else "Serial"
                await message.answer(
                    f"🔔 <b>\"{s_title}\" serialiga muvaffaqiyatli obuna bo'ldingiz!</b>\n\n"
                    f"Yangi qism chiqishi bilanoq sizga birinchilardan bo'lib poster va video havolasi bilan xabar beramiz.",
                    parse_mode="HTML"
                )
                if series:
                    await send_series_info(message.bot, message.from_user.id, series)
                return
            except Exception as e:
                logger.warning(f"Error handling start sub_series_: {e}")

        # Check if it's collection / franchise subscription from web
        if raw_code.startswith("sub_col_"):
            try:
                col_id = int(raw_code.replace("sub_col_", ""))
                is_sub = await api_client.check_collection_subscription(col_id, message.from_user.id)
                if not is_sub:
                    await api_client.toggle_collection_subscription(col_id, message.from_user.id)
                col = await api_client.get_collection(col_id)
                c_name = col.get("name", "Franshiza") if col else "Franshiza"
                await message.answer(
                    f"🔔 <b>\"{c_name}\" franshizasiga muvaffaqiyatli obuna bo'ldingiz!</b>\n\n"
                    f"Yangi qism yoki film qo'shilishi bilanoq sizga birinchilardan bo'lib xabar beramiz.",
                    parse_mode="HTML"
                )
                from utils.info_sender import send_collection_info
                if col:
                    await send_collection_info(message.bot, message.from_user.id, col)
                return
            except Exception as e:
                logger.warning(f"Error handling start sub_col_: {e}")
        
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
            "🔍 <i>Qidirish uchun '🔍 Qidirish' tugmasini bosing yoki kino kodini yuboring.</i>"
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


