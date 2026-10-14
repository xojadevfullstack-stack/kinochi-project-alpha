from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery
from services.api_client import api_client
from keyboards.inline import build_search_results_keyboard
from utils.movie_sender import send_movie_to_user
from config import settings
import html

router = Router()

@router.message(StateFilter(None), F.text & ~F.text.startswith("/") & (F.chat.type == "private"))
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
        
    # 1. Avval so'rovni kino, serial yoki qism kodi/ID si sifatida tekshiramiz
    from utils.code_resolver import resolve_and_send_content
    found = await resolve_and_send_content(message.bot, message.from_user.id, query)
    if found:
        return

    # 2. Agar kod topilmasa va matn juda qisqa bo'lsa
    if len(query) < 2:
        await message.answer("❌ <b>Qidiruv xatosi:</b> Kengroq natija olish uchun kamida 2 ta harf kiriting!", parse_mode="HTML")
        return

        
    # Send unified live search request to backend (movies, series, collections)
    search_result = await api_client.live_search(query=query, limit=10)
    combined_results = search_result.get("results", [])

    if not combined_results:
        # Fallback to individual searches if live search empty
        movie_result = await api_client.search_movies(query=query, limit=5)
        series_result = await api_client.search_series(query=query, limit=5)
        for m in movie_result.get("items", []):
            m["type"] = "movie"
            combined_results.append(m)
        for s in series_result.get("items", []):
            s["type"] = "series"
            combined_results.append(s)

    if not combined_results:
        await message.answer("😔 <b>Afsuski, hech narsa topilmadi...</b>\n\nBalki kino yoki serial nomida xato bordir? Boshqacharoq yozib ko'ring yoki saytimizdagi katalogdan izlang!", parse_mode="HTML")
        return
        
    safe_query = html.escape(query)
    keyboard = build_search_results_keyboard(combined_results)
    await message.answer(
        f"🎉 <b>Qidiruv natijalari:</b>\n\nSiz izlagan <i>'{safe_query}'</i> bo'yicha eng sara kino va seriallarni topdim! Pastdagi ro'yxatdan o'zingizga kerakligini tanlang 👇",
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

@router.callback_query(F.data.startswith("sub_series_"))
async def handle_series_subscription(callback: CallbackQuery):
    series_id_str = callback.data.split("_", 2)[2]
    series_id = int(series_id_str)
    
    res = await api_client.toggle_series_subscription(series_id, callback.from_user.id)
    is_sub = res.get("is_subscribed", False)
    
    if is_sub:
        await callback.answer("🔔 Obuna bo'ldingiz! Yangi qism chiqishi bilan xabar yuboramiz.", show_alert=True)
    else:
        await callback.answer("🔕 Obuna bekor qilindi.", show_alert=True)
        
    # Refresh series card to reflect new subscription button state
    series = await api_client.get_series_by_id(series_id)
    if series:
        from utils.info_sender import send_series_info
        await send_series_info(callback.bot, callback.from_user.id, series, edit_message_id=callback.message.message_id)


# ── Telegram Inline Search Handler ──────────────────────────────────
from aiogram.types import InlineQuery, InlineQueryResultArticle, InputTextMessageContent, InlineKeyboardMarkup, InlineKeyboardButton

@router.inline_query()
async def handle_inline_search(inline_query: InlineQuery):
    query = inline_query.query.strip()
    if not query or len(query) < 2:
        return

    try:
        search_result = await api_client.live_search(query=query, limit=15)
        combined_results = search_result.get("results", [])
    except Exception as e:
        logger.error(f"Inline search error: {e}")
        combined_results = []

    results = []
    for item in combined_results:
        c_type = item.get("type", "movie")
        title = item.get("title", "Nomsiz")
        year = item.get("release_year")
        code = item.get("code")
        item_id = item.get("id")
        poster_url = item.get("poster_url")
        desc = f"{year} • {c_type.capitalize()}" if year else c_type.capitalize()

        deep_link = f"https://t.me/{settings.BOT_USERNAME or 'kinochi_mvp_bot'}?start={code if code else f's_{item_id}'}"
        web_link = f"{settings.WEBSITE_URL}/{c_type}/{code if code else item_id}"

        msg_text = (
            f"🎬 <b>{html.escape(title)}</b>\n\n"
            f"📅 <b>Yili:</b> {year or 'N/A'}\n"
            f"🔑 <b>Kodi:</b> <code>{code or f's_{item_id}'}</code>\n\n"
            f"<i>Kinochi platformasida eng sara sifatda tomosha qiling!</i>"
        )

        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="▶️ Botda ochish", url=deep_link),
                InlineKeyboardButton(text="🌐 Saytda ko'rish", url=web_link)
            ]
        ])

        results.append(
            InlineQueryResultArticle(
                id=f"{c_type}_{item_id}",
                title=title,
                description=desc,
                thumbnail_url=poster_url if (poster_url and poster_url.startswith("http")) else None,
                input_message_content=InputTextMessageContent(
                    message_text=msg_text,
                    parse_mode="HTML"
                ),
                reply_markup=keyboard
            )
        )

    await inline_query.answer(results, cache_time=30, is_personal=True)

