from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from services.api_client import api_client
from keyboards.inline import build_search_results_keyboard
from utils.movie_sender import send_movie_to_user
from config import settings

router = Router()

@router.message(F.text & ~F.text.startswith("/"))
async def handle_search_query(message: Message):
    query = message.text.strip()
    
    if query == "🔍 Kino qidirish":
        await message.answer("🍿 <b>Kino olamiga xush kelibsiz!</b>\n\nQidirmoqchi bo'lgan kinongiz nomini yoki maxsus kodini yuboring. Eng sifatli va yangi kinolar faqat bizda!", parse_mode="HTML")
        return
    elif query == "🎲 Tavsiya kino":
        await message.answer("🔥 <b>Tez kunda...</b>\n\nSiz uchun maxsus tavsiyalar, yilning eng qizg'in premyeralari ro'yxatini tayyorlayapmiz! Biz bilan qoling, zerikishga vaqt bo'lmaydi 😉", parse_mode="HTML")
        return
    elif query == "🌐 Saytga o'tish":
        await message.answer(f"🌐 <b>Katta ekraningiz — bizning sayt!</b>\n\nBarcha filmlar, qulay izlash tizimi va premium dizayn bizning veb-sahifada:\n👉 <b>{settings.WEBSITE_URL}</b>\n\n<i>Kiring, tanlang va mazza qilib tomosha qiling!</i>", parse_mode="HTML")
        return
        
    # Do not search if query is too short
    if len(query) < 2:
        await message.answer("❌ <b>Qidiruv xatosi:</b> Kengroq natija olish uchun kamida 2 ta harf kiriting!", parse_mode="HTML")
        return
        
    from utils.info_sender import send_movie_info, send_series_info
    
    # First, try to see if the query is a code
    movie = await api_client.get_movie_by_code(query)
    if movie:
        success = await send_movie_info(message.bot, message.from_user.id, movie)
        if not success:
            await message.answer("Kechirasiz, xatolik yuz berdi.")
        return
        
    episode = await api_client.get_episode_by_code(query)
    if episode:
        # If they searched episode code directly, we should fetch the series and show series info to let them select season/episode, or just show season info?
        # A better approach: if they search an episode code, they probably just want to watch it directly. Let's send the episode video directly since it's an exact episode code.
        from utils.episode_sender import send_episode_to_user
        success = await send_episode_to_user(message.bot, message.from_user.id, episode)
        if not success:
            await message.answer("Kechirasiz, ushbu qism videosi hali yuklanmagan yoki xatolik yuz berdi.")
        return
        
    # Send search request to backend for movies and series
    movie_result = await api_client.search_movies(query=query, limit=10)
    series_result = await api_client.search_series(query=query, limit=10)
    
    movies = movie_result.get("items", [])
    series = series_result.get("items", [])
    
    # Combine results and tag with type
    combined_results = []
    for m in movies:
        m['type'] = 'movie'
        combined_results.append(m)
    for s in series:
        s['type'] = 'series'
        combined_results.append(s)
        
    if not combined_results:
        await message.answer("😔 <b>Afsuski, hech narsa topilmadi...</b>\n\nBalki kino yoki serial nomida xato bordir? Boshqacharoq yozib ko'ring yoki saytimizdagi katalogdan izlang!", parse_mode="HTML")
        return
        
    keyboard = build_search_results_keyboard(combined_results)
    await message.answer(
        f"🎉 <b>Qidiruv natijalari:</b>\n\nSiz izlagan <i>'{query}'</i> bo'yicha eng sara kino va seriallarni topdim! Pastdagi ro'yxatdan o'zingizga kerakligini tanlang 👇",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("movie_"))
async def handle_movie_selection(callback: CallbackQuery):
    code = callback.data.split("_", 1)[1]
    
    await callback.answer() # Acknowledge callback
    
    movie = await api_client.get_movie_by_code(code)
    
    if not movie:
        await callback.message.answer("⚠️ <b>Xatolik:</b> Bu kino bazadan topilmadi. Balki o'chirilgandir?", parse_mode="HTML")
        return
        
    from utils.info_sender import send_movie_info
    success = await send_movie_info(callback.bot, callback.from_user.id, movie)
    
    if not success:
        await callback.message.answer("⚠️ Xatolik yuz berdi.", parse_mode="HTML")

@router.callback_query(F.data.startswith("search_series_"))
async def handle_series_selection(callback: CallbackQuery):
    series_id_str = callback.data.split("_", 2)[2]
    
    await callback.answer() # Acknowledge callback
    
    series_id = int(series_id_str)
    series = await api_client.get_series_by_id(series_id)
    
    if not series:
        await callback.message.answer("⚠️ <b>Xatolik:</b> Bu serial bazadan topilmadi. Balki o'chirilgandir?", parse_mode="HTML")
        return
        
    from utils.info_sender import send_series_info
    success = await send_series_info(callback.bot, callback.from_user.id, series)
    
    if not success:
        await callback.message.answer("⚠️ Xatolik yuz berdi.", parse_mode="HTML")
