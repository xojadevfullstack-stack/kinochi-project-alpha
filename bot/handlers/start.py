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
        code = args.strip()
        
        # Check if it's login
        if code.lower() == "login":
            return await cmd_login(message)
        
        # Check if it's a series ID (starts with s_)
        if code.startswith("s_"):
            series_id = code[2:]
            series = await api_client.get_series_by_id(series_id)
            if series:
                success = await send_series_info(message.bot, message.from_user.id, series)
                if not success:
                    await message.answer("Kechirasiz, ushbu serial haqida ma'lumot topilmadi.")
                return
            await message.answer("❌ <b>Hech narsa topilmadi!</b>", parse_mode="HTML")
            return
            
        # 1. Try fetching as a movie
        movie = await api_client.get_movie_by_code(code)
        if movie:
            success = await send_movie_info(message.bot, message.from_user.id, movie)
            if not success:
                await message.answer("Kechirasiz, ushbu kino haqida ma'lumot topilmadi.")
            return

        # 2. Try fetching as an episode
        from utils.info_sender import send_season_info
        episode = await api_client.get_episode_by_code(code)
        if episode:
            # Send the season menu instead of the video directly
            season_id = episode.get("season_id")
            series_id = episode.get("series_id")
            # We would need to fetch the season info. But wait, getting episode is not usually what the website links to.
            # The website links to series or movie. Let's just keep the old behavior for episodes or send video.
            from utils.episode_sender import send_episode_to_user
            success = await send_episode_to_user(message.bot, message.from_user.id, episode)
            if not success:
                await message.answer("Kechirasiz, ushbu qism videosi hali yuklanmagan yoki xatolik yuz berdi.")
            return

        # 3. If neither found
        await message.answer("❌ <b>Hech narsa topilmadi!</b>\n\nSiz yuborgan kod bo'yicha ma'lumot topilmadi. Kodni to'g'ri yozganingizga ishonch hosil qiling!", parse_mode="HTML")
    else:
        welcome_text = (
            "👋 <b>Kinochi botiga xush kelibsiz!</b>\n\n"
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


