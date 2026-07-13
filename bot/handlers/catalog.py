from aiogram import Router, F
from aiogram.types import Message
from services.api_client import api_client
from utils.info_sender import send_movie_info, send_series_info
from keyboards.reply import catalog_menu, main_menu

router = Router()

@router.message(F.text == "📂 Katalog")
async def handle_catalog_btn(message: Message):
    await message.answer("📂 Kategoriyalardan birini tanlang:", reply_markup=catalog_menu)

@router.message(F.text == "🔙 Asosiy menyu")
async def handle_back_to_main(message: Message):
    await message.answer("Siz asosiy menyudasiz.", reply_markup=main_menu)

@router.message(F.text == "🎬 Kinolar")
async def handle_movies_catalog(message: Message):
    # Fetch latest movies (limit 5 for telegram UI friendliness)
    data = await api_client.get_movies(limit=5)
    movies = data.get("items", [])
    
    if not movies:
        await message.answer("Hozircha kinolar mavjud emas.")
        return
        
    await message.answer("🎬 <b>Eng so'nggi kinolar:</b>", parse_mode="HTML")
    for movie in movies:
        await send_movie_info(message.bot, message.chat.id, movie)

@router.message(F.text == "📺 Seriallar")
async def handle_series_catalog(message: Message):
    # Fetch latest series
    data = await api_client.get_series(limit=5)
    series_list = data.get("items", [])
    
    if not series_list:
        await message.answer("Hozircha seriallar mavjud emas.")
        return
        
    await message.answer("📺 <b>Eng so'nggi seriallar:</b>", parse_mode="HTML")
    for series in series_list:
        await send_series_info(message.bot, message.chat.id, series)
