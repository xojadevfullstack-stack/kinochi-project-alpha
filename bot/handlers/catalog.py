from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.api_client import api_client
from utils.info_sender import send_movie_info, send_series_info
from keyboards.inline import get_main_menu_inline, get_catalog_categories_inline, build_catalog_items_list
from config import settings

router = Router()

def get_webapp_url():
    webapp_url = settings.WEBSITE_URL
    if not webapp_url.startswith("https://"):
        webapp_url = "https://kinochi-project-alpha.vercel.app/"
    return webapp_url

@router.callback_query(F.data == "menu_catalog")
async def handle_catalog_btn(callback: CallbackQuery):
    text = "📂 Kategoriyalardan birini tanlang:"
    markup = get_catalog_categories_inline()
    try:
        if callback.message.photo or callback.message.video:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=markup)
        else:
            await callback.message.edit_text(text, reply_markup=markup)
    except Exception:
        await callback.message.answer(text, reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data == "menu_main")
async def handle_back_to_main(callback: CallbackQuery):
    welcome_text = (
        "👋 <b>Kinochi botiga xush kelibsiz!</b>\n\n"
        "🎬 Eng sara kinolar va seriallar aynan shu yerda.\n"
        "🎥 Kinoni ko'rish uchun menyudan tanlang yoki izlang!\n\n"
        "🔍 <i>Qidirish uchun shunchaki kino nomini yozing.</i>"
    )
    try:
        if callback.message.photo or callback.message.video:
            await callback.message.delete()
            await callback.message.answer(
                welcome_text, 
                reply_markup=get_main_menu_inline(get_webapp_url()),
                parse_mode="HTML"
            )
        else:
            await callback.message.edit_text(
                welcome_text, 
                reply_markup=get_main_menu_inline(get_webapp_url()),
                parse_mode="HTML"
            )
    except Exception:
        await callback.message.answer(
            welcome_text, 
            reply_markup=get_main_menu_inline(get_webapp_url()),
            parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(F.data == "menu_movies")
async def handle_movies_catalog(callback: CallbackQuery):
    # Fetch latest movies (limit 10 for telegram UI friendliness)
    data = await api_client.get_movies(limit=10)
    movies = data.get("items", [])
    
    if not movies:
        await callback.answer("Hozircha kinolar mavjud emas.", show_alert=True)
        return
        
    await callback.message.edit_text(
        "🎬 <b>Eng so'nggi kinolar:</b>\n<i>Quyidagi ro'yxatdan birini tanlang:</i>", 
        parse_mode="HTML",
        reply_markup=build_catalog_items_list(movies, "movie")
    )
    await callback.answer()

@router.callback_query(F.data == "menu_series")
async def handle_series_catalog(callback: CallbackQuery):
    # Fetch latest series
    data = await api_client.get_series(limit=10)
    series_list = data.get("items", [])
    
    if not series_list:
        await callback.answer("Hozircha seriallar mavjud emas.", show_alert=True)
        return
        
    await callback.message.edit_text(
        "📺 <b>Eng so'nggi seriallar:</b>\n<i>Quyidagi ro'yxatdan birini tanlang:</i>", 
        parse_mode="HTML",
        reply_markup=build_catalog_items_list(series_list, "series")
    )
    await callback.answer()

@router.callback_query(F.data.startswith("catalog_item_movie_"))
async def handle_catalog_movie_select(callback: CallbackQuery):
    movie_id = int(callback.data.split("_")[-1])
    movie = await api_client.get_movie_by_id(movie_id)
    if not movie:
        await callback.answer("Kino topilmadi", show_alert=True)
        return
    
    # Send movie info as a new message, delete the catalog message to keep it clean?
    # Or just send it. Let's send as new message and optionally delete old one.
    try:
        await callback.message.delete()
    except:
        pass
    
    await send_movie_info(callback.bot, callback.from_user.id, movie)
    await callback.answer()

@router.callback_query(F.data.startswith("catalog_item_series_"))
async def handle_catalog_series_select(callback: CallbackQuery):
    series_id = int(callback.data.split("_")[-1])
    series = await api_client.get_series_by_id(series_id)
    if not series:
        await callback.answer("Serial topilmadi", show_alert=True)
        return
        
    try:
        await callback.message.delete()
    except:
        pass
        
    await send_series_info(callback.bot, callback.from_user.id, series)
    await callback.answer()

@router.callback_query(F.data == "help_search")
async def handle_help_search(callback: CallbackQuery):
    await callback.answer("Shunchaki chatga kino yoki serial nomini yozib yuboring!", show_alert=True)
