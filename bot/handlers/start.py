from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message
from services.api_client import api_client
from utils.movie_sender import send_movie_to_user
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
        
        # 1. Try fetching as a movie
        movie = await api_client.get_movie_by_code(code)
        if movie:
            success = await send_movie_to_user(message.bot, message.from_user.id, movie)
            if not success:
                await message.answer("Kechirasiz, ushbu kino videosi hali yuklanmagan yoki xatolik yuz berdi.")
            return

        # 2. Try fetching as an episode
        from utils.episode_sender import send_episode_to_user
        episode = await api_client.get_episode_by_code(code)
        if episode:
            success = await send_episode_to_user(message.bot, message.from_user.id, episode)
            if not success:
                await message.answer("Kechirasiz, ushbu qism videosi hali yuklanmagan yoki xatolik yuz berdi.")
            return

        # 3. If neither found
        await message.answer("❌ <b>Hech narsa topilmadi!</b>\n\nSiz yuborgan kod bo'yicha kino yoki serial qismi topilmadi. Kodni to'g'ri yozganingizga ishonch hosil qiling!", parse_mode="HTML")
    else:
        welcome_text = (
            "👋 <b>Kinochi botiga xush kelibsiz!</b>\n\n"
            "🎬 Eng sara kinolar va seriallar aynan shu yerda.\n"
            "🎥 Kinoni ko'rish uchun menyudan tanlang yoki izlang!\n\n"
            "🔍 <i>Qidirish uchun shunchaki kino nomini yozing.</i>"
        )
        
        webapp_url = settings.WEBSITE_URL
        if not webapp_url.startswith("https://"):
            webapp_url = "https://kinochi-project-alpha.vercel.app/"
            
        await message.answer(welcome_text, parse_mode="HTML", reply_markup=get_main_menu_inline(webapp_url))
