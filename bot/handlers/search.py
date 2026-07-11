from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from services.api_client import api_client
from keyboards.inline import build_movies_list_keyboard
from utils.movie_sender import send_movie_to_user

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
        await message.answer("🌐 <b>Katta ekraningiz — bizning sayt!</b>\n\nBarcha filmlar, qulay izlash tizimi va premium dizayn bizning veb-sahifada:\n👉 <b>http://localhost:3000</b>\n\n<i>Kiring, tanlang va mazza qilib tomosha qiling!</i>", parse_mode="HTML")
        return
        
    # Do not search if query is too short
    if len(query) < 2:
        await message.answer("❌ <b>Qidiruv xatosi:</b> Kengroq natija olish uchun kamida 2 ta harf kiriting!", parse_mode="HTML")
        return
        
    # Send search request to backend
    result = await api_client.search_movies(query=query, limit=10)
    movies = result.get("items", [])
    
    if not movies:
        await message.answer("😔 <b>Afsuski, hech narsa topilmadi...</b>\n\nBalki kino nomida xato bordir? Boshqacharoq yozib ko'ring yoki saytimizdagi katalogdan izlang!", parse_mode="HTML")
        return
        
    keyboard = build_movies_list_keyboard(movies)
    await message.answer(
        f"🎉 <b>Qidiruv natijalari:</b>\n\nSiz izlagan <i>'{query}'</i> bo'yicha eng sara kinolarni topdim! Pastdagi ro'yxatdan o'zingizga kerakligini tanlang 👇",
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
        
    success = await send_movie_to_user(callback.bot, callback.from_user.id, movie)
    
    if not success:
        await callback.message.answer("⏳ <b>Kino tayyorlanmoqda...</b>\n\nBu kinoning videosi tez orada bazaga yuklanadi. Kuting va keyinroq qayta urinib ko'ring!", parse_mode="HTML")
