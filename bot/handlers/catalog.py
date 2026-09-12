from aiogram import Router, F
from aiogram.types import CallbackQuery
from services.api_client import api_client
from utils.info_sender import send_movie_info, send_series_info
from keyboards.inline import get_main_menu_inline, get_catalog_categories_inline, build_catalog_items_list, build_page_items_list
from config import settings
import logging

logger = logging.getLogger(__name__)

router = Router()

def get_webapp_url():
    return "https://kinochi-project-alpha.vercel.app/"

@router.callback_query(F.data == "menu_catalog")
async def handle_catalog_btn(callback: CallbackQuery):
    text = "📂 Kategoriyalardan birini tanlang:"
    
    pages_data = await api_client.get_pages()
    pages = pages_data.get("items", [])
    
    markup = get_catalog_categories_inline(pages)
    try:
        if callback.message.photo or callback.message.video:
            await callback.message.delete()
            await callback.message.answer(text, reply_markup=markup)
        else:
            await callback.message.edit_text(text, reply_markup=markup)
    except Exception as e:
        logger.warning(f"Error in handle_catalog_btn: {e}")
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
    except Exception as e:
        logger.warning(f"Error in handle_back_to_main: {e}")
        await callback.message.answer(
            welcome_text, 
            reply_markup=get_main_menu_inline(get_webapp_url()),
            parse_mode="HTML"
        )
    await callback.answer()

@router.callback_query(F.data == "catalog_all_movies")
async def handle_catalog_all_movies(callback: CallbackQuery):
    movies_data = await api_client.get_movies(limit=10)
    items = movies_data.get("items", [])
    if not items:
        await callback.answer("Hozircha kinolar mavjud emas.", show_alert=True)
        return
    text = "🎬 <b>Kinolar ro'yxati:</b>\n<i>Quyidagi kinolardan birini tanlang:</i>"
    markup = build_catalog_items_list(items, "movie")
    try:
        if callback.message.photo or callback.message.video:
            await callback.message.delete()
            await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
        else:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        logger.warning(f"Error in handle_catalog_all_movies: {e}")
        await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data == "catalog_all_series")
async def handle_catalog_all_series(callback: CallbackQuery):
    series_data = await api_client.get_series(limit=10)
    items = series_data.get("items", [])
    if not items:
        await callback.answer("Hozircha seriallar mavjud emas.", show_alert=True)
        return
    text = "📺 <b>Seriallar ro'yxati:</b>\n<i>Quyidagi seriallardan birini tanlang:</i>"
    markup = build_catalog_items_list(items, "series")
    try:
        if callback.message.photo or callback.message.video:
            await callback.message.delete()
            await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
        else:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        logger.warning(f"Error in handle_catalog_all_series: {e}")
        await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
    await callback.answer()

@router.callback_query(F.data.startswith("menu_page_"))
async def handle_page_catalog(callback: CallbackQuery):
    page_id = int(callback.data.split("_")[-1])
    
    # Fetch movies and series for this page
    movies_data = await api_client.get_movies(limit=10, page_id=page_id)
    series_data = await api_client.get_series(limit=10, page_id=page_id)
    
    results = []
    for m in movies_data.get("items", []):
        m["type"] = "movie"
        results.append(m)
    for s in series_data.get("items", []):
        s["type"] = "series"
        results.append(s)
        
    if not results:
        await callback.answer("Hozircha ushbu sahifada hech narsa yo'q.", show_alert=True)
        return
        
    text = "📂 <b>Sahifa natijalari:</b>\n<i>Quyidagi ro'yxatdan birini tanlang:</i>"
    markup = build_page_items_list(results)
    try:
        if callback.message.photo or callback.message.video:
            await callback.message.delete()
            await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
        else:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
    except Exception as e:
        logger.warning(f"Error in handle_page_catalog: {e}")
        await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
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
    except Exception as e:
        logger.warning(f"Could not delete message in handle_catalog_movie_select: {e}")
    
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
    except Exception as e:
        logger.warning(f"Could not delete message in handle_catalog_series_select: {e}")
        
    await send_series_info(callback.bot, callback.from_user.id, series)
    await callback.answer()

@router.callback_query(F.data == "help_search")
async def handle_help_search(callback: CallbackQuery):
    await callback.answer("Shunchaki chatga kino yoki serial nomini yozib yuboring!", show_alert=True)
