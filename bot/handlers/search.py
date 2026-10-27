from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery, WebAppInfo
from services.api_client import api_client
from keyboards.inline import build_search_results_keyboard
from utils.movie_sender import send_movie_to_user
from config import settings
import html
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.message(StateFilter(None), F.text & ~F.text.startswith("/") & (F.chat.type == "private"))
async def handle_search_query(message: Message):
    query = message.text.strip()
    
    # 0. Agar xabar inline qidiruvdan ulashilgan xabar bo'lsa yoki bot xabari bo'lsa, e'tiborsiz qoldiramiz
    if any(keyword in query for keyword in [
        "platformamiz bazasida hali mavjud emas",
        "Kinochi platformasida",
        "Kinolar qidiruvi Inline",
        "bo'yicha kinolar va seriallarni jonli topish"
    ]):
        return
    
    if query == "🔍 Kino qidirish":
        await message.answer("🍿 <b>Kino olamiga xush kelibsiz!</b>\n\nQidirmoqchi bo'lgan kinongiz nomini yoki maxsus kodini yuboring. Eng sifatli va yangi kinolar faqat bizda!", parse_mode="HTML")
        return
    elif query == "🎲 Tavsiya kino":
        await message.answer("🔥 <b>Tez kunda...</b>\n\nSiz uchun maxsus tavsiyalar, yilning eng qizg'in premyeralari ro'yxatini tayyorlayapmiz! Biz bilan qoling, zerikishga vaqt bo'lmaydi 😉", parse_mode="HTML")
        return
    elif query == "🌐 Saytga o'tish":
        await message.answer(f"🌐 <b>Katta ekraningiz — bizning sayt!</b>\n\nBarcha filmlar, qulay izlash tizimi va premium dizayn bizning veb-sahifada:\n👉 <b>{settings.WEBSITE_URL}</b>\n\n<i>Kiring, tanlang va mazza qilib tomosha qiling!</i>", parse_mode="HTML")
        return
    elif query.lower() in ["katalog", "📂 katalog", "ortga", "◀️ ortga", "orqaga", "🔙 katalog", "🔙 katalogga qaytish"]:
        from handlers.catalog import send_catalog
        await send_catalog(message)
        return
        
    # 1. Avval so'rovni kino, serial yoki qism kodi/ID si sifatida tekshiramiz
    from utils.code_resolver import resolve_and_send_content
    found = await resolve_and_send_content(message.bot, message.from_user.id, query)
    if found:
        return

    # 2. Ichki bazadan tezkor jonli qidiramiz
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    base_site = getattr(settings, "WEBSITE_URL", "https://kinochi-project-alpha.vercel.app").rstrip("/")
    
    try:
        live_res = await api_client.live_search(query=query, limit=5)
        local_results = live_res.get("results", [])
    except Exception as e:
        logger.warning(f"Local live search error in bot: {e}")
        local_results = []

    if local_results:
        buttons = []
        for it in local_results:
            c_type = it.get("type", "movie")
            title = it.get("title", "Nomsiz")
            year = it.get("year")
            y_str = f" ({year})" if year else ""
            
            if c_type == "movie":
                code = it.get("code")
                buttons.append([InlineKeyboardButton(text=f"🎬 {title}{y_str}", callback_data=f"movie_{code}")])
            elif c_type == "series":
                s_id = it.get("id")
                buttons.append([InlineKeyboardButton(text=f"📺 {title}{y_str}", callback_data=f"search_series_{s_id}")])
            elif c_type == "collection":
                slug = it.get("code") or str(it.get("id"))
                buttons.append([InlineKeyboardButton(text=f"🌌 {title}", url=f"{base_site}/collections/{slug}")])

        buttons.append([InlineKeyboardButton(text="🌐 Saytda to'liq qidirish", url=f"{base_site}/search?q={query}")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            f"🔍 <b>'{html.escape(query)}'</b> bo'yicha bazamizdan topilgan natijalar:\n\n"
            f"Kerakli film yoki serialni tanlang 👇",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return

    # 3. Ichki bazada yo'q bo'lsa, TMDB va Kinopoisk orqali tashqi qidiramiz
    try:
        ext_res = await api_client.external_search(query=query, limit=4)
        ext_items = ext_res.get("results", [])
    except Exception as e:
        logger.warning(f"External search error in bot: {e}")
        ext_items = []

    if ext_items:
        buttons = []
        for it in ext_items:
            e_id = it.get("tmdb_id") or it.get("kinopoisk_id")
            e_title = it.get("title", "Nomsiz")
            e_year = it.get("release_year")
            e_type = it.get("media_type", "movie")
            y_str = f" ({e_year})" if e_year else ""
            cnt = it.get("request_count", 0)
            cnt_str = f" • {cnt} so'rov" if cnt > 0 else ""
            
            # Short safe title for callback data (max 20 chars to fit within 64 byte limit)
            safe_cb_title = e_title[:20].replace(":", "")
            buttons.append([
                InlineKeyboardButton(
                    text=f"📥 {e_title[:22]}{y_str}{cnt_str}",
                    callback_data=f"req_tmdb:{e_type}:{e_id}:{safe_cb_title}"
                )
            ])

        buttons.append([InlineKeyboardButton(text="🌐 Saytda so'rov qoldirish", url=f"{base_site}/requests")])
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer(
            f"🎬 <b>'{html.escape(query)}'</b> bizning platformamizda hali mavjud emas.\n\n"
            f"Lekin jahon katalogidan (TMDB) topildi! Uni birinchi navbatda yuklashimizni xohlasangiz, pastdagi <b>'Qo'shishni so'rash'</b> tugmasini bosing 👇",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return

    # 4. Agar umuman hech qayerdan topilmasa
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📥 Saytda so'rov qoldirish", url=f"{base_site}/requests")],
        [InlineKeyboardButton(text="🌐 Bosh sahifaga o'tish", url=base_site)]
    ])
    await message.answer(
        f"😔 <b>'{html.escape(query)}'</b> bo'yicha hech qanday film yoki serial topilmadi.\n\n"
        f"Nomini to'g'ri yozganingizni tekshiring yoki saytimiz orqali adminlarga buyurtma qoldiring 👇",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("movie_"))
async def handle_movie_selection(callback: CallbackQuery):
    try:
        code = callback.data.split("_", 1)[1]
        
        movie = await api_client.get_movie_by_code(code)
        
        if not movie:
            await callback.message.answer("⚠️ <b>Xatolik:</b> Bu kino bazadan topilmadi. Balki o'chirilgandir?", parse_mode="HTML")
            return
            
        from utils.info_sender import send_movie_info
        success = await send_movie_info(callback.bot, callback.from_user.id, movie)
        
        if not success:
            await callback.message.answer("⚠️ Xatolik yuz berdi.", parse_mode="HTML")
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

@router.callback_query(F.data.startswith("search_series_"))
async def handle_series_selection(callback: CallbackQuery):
    try:
        series_id_str = callback.data.split("_", 2)[2]
        
        series_id = int(series_id_str)
        series = await api_client.get_series_by_id(series_id)
        
        if not series:
            await callback.message.answer("⚠️ <b>Xatolik:</b> Bu serial bazadan topilmadi. Balki o'chirilgandir?", parse_mode="HTML")
            return
            
        from utils.info_sender import send_series_info
        success = await send_series_info(callback.bot, callback.from_user.id, series)
        
        if not success:
            await callback.message.answer("⚠️ Xatolik yuz berdi.", parse_mode="HTML")
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

@router.callback_query(F.data.startswith("sub_series_"))
async def handle_series_subscription(callback: CallbackQuery):
    try:
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
    finally:
        try:
            await callback.answer()
        except Exception:
            pass


@router.callback_query(F.data.startswith("sub_col_"))
async def handle_collection_subscription(callback: CallbackQuery):
    try:
        parts = callback.data.split("_")
        col_id = int(parts[2])
        movie_code = parts[3] if len(parts) > 3 else None

        res = await api_client.toggle_collection_subscription(col_id, callback.from_user.id)
        is_sub = res.get("is_subscribed", False)

        col = await api_client.get_collection(col_id)
        col_name = col.get("name", "To'plam") if col else "To'plam"

        if is_sub:
            await callback.answer(f"🔔 Obuna bo'ldingiz!\n\n'{col_name}'ga yangi film qo'shilsa xabar yuboramiz.", show_alert=True)
        else:
            await callback.answer(f"🔕 '{col_name}' obunasi bekor qilindi.", show_alert=True)

        if movie_code:
            movie = await api_client.get_movie_by_code(movie_code)
            if movie:
                from utils.info_sender import send_movie_info
                await send_movie_info(callback.bot, callback.from_user.id, movie, edit_message_id=callback.message.message_id)
    except Exception as e:
        logger.warning(f"Error in handle_collection_subscription: {e}")
    finally:
        try:
            await callback.answer()
        except Exception:
            pass


@router.callback_query(F.data.startswith("col_view_"))
async def handle_collection_view(callback: CallbackQuery):
    try:
        col_id = int(callback.data.split("_", 2)[2])
        col = await api_client.get_collection(col_id)
        if not col:
            await callback.answer("To'plam topilmadi", show_alert=True)
            return

        from utils.info_sender import send_collection_info
        await send_collection_info(callback.bot, callback.from_user.id, col, edit_message_id=callback.message.message_id)
    except Exception as e:
        logger.warning(f"Error in handle_collection_view: {e}")
    finally:
        try:
            await callback.answer()
        except Exception:
            pass


# ── Telegram Inline Search Handler ──────────────────────────────────
from aiogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultsButton,
)

@router.inline_query()
async def handle_inline_search(inline_query: InlineQuery):
    query = inline_query.query.strip()
    bot_username = getattr(settings, "BOT_USERNAME", "kinochi_mvp_bot").lstrip("@")
    base_site = getattr(settings, "WEBSITE_URL", "https://kinochi-project-alpha.vercel.app").rstrip("/")
    if not base_site or "localhost" in base_site or "127.0.0.1" in base_site:
        base_site = "https://kinochi-project-alpha.vercel.app"

    # 1. So'rov bo'sh bo'lganda ko'rsatma tugmasi
    if not query:
        try:
            await inline_query.answer(
                results=[],
                cache_time=5,
                is_personal=False,
                button=InlineQueryResultsButton(
                    text="🔍 Kino yoki serial nomini yozing...",
                    start_parameter="search"
                )
            )
        except Exception as e:
            logger.warning(f"Empty inline query answer error: {e}")
        return

    # 2. 2 ta harfdan kam bo'lganda ogohlantirish
    if len(query) < 2:
        try:
            await inline_query.answer(
                results=[],
                cache_time=5,
                is_personal=False,
                button=InlineQueryResultsButton(
                    text="⚠️ Kamida 2 ta harf yozing...",
                    start_parameter="search"
                )
            )
        except Exception as e:
            logger.warning(f"Short inline query answer error: {e}")
        return

    try:
        search_result = await api_client.live_search(query=query, limit=15)
        combined_results = search_result.get("results", [])
    except Exception as e:
        logger.error(f"Inline search error: {e}", exc_info=True)
        combined_results = []

    # Agar live_search bo'sh qaytarsa, alohida kinolar va seriallarni qidirib ko'ramiz
    if not combined_results:
        try:
            m_res = await api_client.search_movies(query=query, limit=8)
            s_res = await api_client.search_series(query=query, limit=8)
            for m in m_res.get("items", []):
                m["type"] = "movie"
                combined_results.append(m)
            for s in s_res.get("items", []):
                s["type"] = "series"
                combined_results.append(s)
        except Exception as e:
            logger.error(f"Inline search fallback error: {e}", exc_info=True)

    results = []

    # 3. Agar ichki bazada hech narsa topilmasa, TMDB / Tashqi bazadan qidiramiz
    if not combined_results:
        safe_q = html.escape(query[:40])
        try:
            ext_search = await api_client.external_search(query=query, limit=5)
            ext_results = ext_search.get("results", [])
        except Exception as e:
            logger.warning(f"External search error: {e}")
            ext_results = []

        if ext_results:
            for ext in ext_results:
                e_id = ext.get("tmdb_id") or ext.get("kinopoisk_id")
                e_title = ext.get("title") or "Nomsiz"
                e_year = ext.get("release_year") or "N/A"
                e_type = ext.get("media_type") or "movie"
                e_rating = ext.get("vote_average")
                r_str = f" ⭐ {e_rating:.1f}" if e_rating else ""
                req_cnt = ext.get("request_count", 0)

                results.append(
                    InlineQueryResultArticle(
                        id=f"ext_{e_id}",
                        title=f"🎬 [Bazada yo'q] {e_title} ({e_year})",
                        description=f"TMDB katalogidan • Qo'shishni so'rash ({req_cnt} ta so'rov){r_str}",
                        thumbnail_url=ext.get("poster_url"),
                        input_message_content=InputTextMessageContent(
                            message_text=(
                                f"🎬 <b>{html.escape(e_title)}</b> ({e_year})\n\n"
                                f"ℹ️ <i>Ushbu film/serial platformamiz bazasida hali mavjud emas.</i>\n\n"
                                "Adminlarimiz uni birinchi navbatda joylashi uchun <b>'Qo'shishni so'rash'</b> tugmasini bosing 👇"
                            ),
                            parse_mode="HTML"
                        ),
                        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text=f"📥 Qo'shishni so'rash ({req_cnt} ta so'rov)", callback_data=f"req_tmdb:{e_type}:{e_id}:{e_title[:20].replace(':', '')}")],
                            [InlineKeyboardButton(text="🌐 Saytda to'liq ko'rish / so'rash", url=f"{base_site}/requests")]
                        ])
                    )
                )
            try:
                await inline_query.answer(results, cache_time=15, is_personal=False)
                return
            except Exception as e:
                logger.warning(f"Ext results inline answer error: {e}")

        # Agar TMDB dan ham topilmasa
        results.append(
            InlineQueryResultArticle(
                id="not_found",
                title=f"😔 '{query[:30]}' topilmadi",
                description="Boshqa nom bilan qidirib ko'ring yoki botga o'ting",
                input_message_content=InputTextMessageContent(
                    message_text=(
                        f"😔 <b>'{safe_q}'</b> bo'yicha hech qanday film yoki serial topilmadi.\n\n"
                        f"Boshqa so'z bilan izlab ko'ring yoki so'rov qoldirish uchun saytimizga o'ting!"
                    ),
                    parse_mode="HTML"
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="📥 Kino qo'shishni so'rash", url=f"{base_site}/requests")],
                    [InlineKeyboardButton(text="🔍 Botda qidirish", url=f"https://t.me/{bot_username}")]
                ])
            )
        )
        try:
            await inline_query.answer(results, cache_time=30, is_personal=False)
        except Exception as e:
            logger.warning(f"Empty results inline answer error: {e}")
        return

    for item in combined_results:
        c_type = item.get("type", "movie")
        title = item.get("title", "Nomsiz")
        year = item.get("release_year") or item.get("year")
        code = item.get("code")
        item_id = item.get("id")
        poster_url = item.get("poster_url")
        rating = item.get("imdb_rating")
        rating_str = f" ⭐ {rating:.1f}" if rating else ""
        genres = item.get("genres") or []
        genre_str = f"\n🎭 <b>Janr:</b> {', '.join(genres[:3])}" if genres else ""

        if c_type == "collection":
            slug = item.get("code") or item.get("slug") or str(item_id)
            desc = "🌌 Xronologiya to'plami"
            web_link = f"{base_site}/collections/{slug}"
            deep_link = f"https://t.me/{bot_username}?start=col_{slug}"
            msg_text = (
                f"🌌 <b>{html.escape(title)}</b> (Franshiza Xronologiyasi)\n\n"
                f"📚 Kinokoinotning barcha qismlarini to'liq voqealar ketma-ketligi bo'yicha tomosha qiling!\n\n"
                f"<i>Kinochi platformasida eng sara sifatda tomosha qiling!</i>"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="▶️ Botda ochish", url=deep_link),
                    InlineKeyboardButton(text="🌐 Franshizani ko'rish", url=web_link),
                ]
            ])
        elif c_type == "series":
            desc = f"📺 Serial • {year or 'N/A'}{rating_str}"
            deep_link = f"https://t.me/{bot_username}?start=s_{item_id}"
            web_link = f"{base_site}/series/{item_id}"
            msg_text = (
                f"📺 <b>{html.escape(title)}</b>\n\n"
                f"📅 <b>Yili:</b> {year or 'N/A'}\n"
                f"🔑 <b>Serial kodi:</b> <code>s_{item_id}</code>"
                f"{rating_str}"
                f"{genre_str}\n\n"
                f"<i>Kinochi platformasida barcha fasl va qismlarni tomosha qiling!</i>"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="▶️ Botda ochish", url=deep_link),
                    InlineKeyboardButton(text="🌐 Saytda ko'rish", url=web_link),
                ]
            ])
        else:
            desc = f"🎬 Kino • {year or 'N/A'}{rating_str}"
            deep_link = f"https://t.me/{bot_username}?start={code}" if code else f"https://t.me/{bot_username}"
            web_link = f"{base_site}/movie/{code or item_id}"
            msg_text = (
                f"🎬 <b>{html.escape(title)}</b>\n\n"
                f"📅 <b>Yili:</b> {year or 'N/A'}\n"
                f"🔑 <b>Kino kodi:</b> <code>{code or 'N/A'}</code>"
                f"{rating_str}"
                f"{genre_str}\n\n"
                f"<i>Kinochi platformasida eng sara sifatda tomosha qiling!</i>"
            )
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="▶️ Botda ochish", url=deep_link),
                    InlineKeyboardButton(text="🌐 Saytda ko'rish", url=web_link),
                ]
            ])

        thumb = poster_url if (poster_url and (poster_url.startswith("http://") or poster_url.startswith("https://"))) else None

        results.append(
            InlineQueryResultArticle(
                id=f"{c_type}_{item_id}",
                title=title,
                description=desc,
                thumbnail_url=thumb,
                input_message_content=InputTextMessageContent(
                    message_text=msg_text,
                    parse_mode="HTML"
                ),
                reply_markup=keyboard
            )
        )

    try:
        await inline_query.answer(results, cache_time=60, is_personal=False)
    except Exception as e:
        logger.error(f"Failed to answer inline query: {e}", exc_info=True)




@router.callback_query(F.data.startswith("req_tmdb:"))
async def handle_request_tmdb_callback(callback: CallbackQuery):
    try:
        parts = callback.data.split(":", 3)
        m_type = parts[1] if len(parts) > 1 else "movie"
        tmdb_id = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else None
        title = parts[3] if len(parts) > 3 and parts[3] else None
        
        user_contact = f"@{callback.from_user.username}" if callback.from_user.username else str(callback.from_user.id)
        res = await api_client.submit_content_request(
            title=title or f"TMDb #{tmdb_id}",
            media_type=m_type,
            tmdb_id=tmdb_id,
            telegram_user_id=callback.from_user.id,
            user_contact=user_contact
        )
        msg = res.get("message") or "✅ So'rovingiz qabul qilindi! Adminlarimiz uni platformaga qo'shishadi."
        await callback.answer(msg, show_alert=True)

        # Tugmani 'So'ralgan' holatiga yangilash
        if callback.message and callback.message.reply_markup:
            new_rows = []
            for row in callback.message.reply_markup.inline_keyboard:
                new_row = []
                for btn in row:
                    if btn.callback_data == callback.data:
                        v_cnt = res.get("vote_count", 1)
                        new_row.append(InlineKeyboardButton(text=f"✅ So'ralgan ({v_cnt} ta ovoz)", callback_data="voted_already"))
                    else:
                        new_row.append(btn)
                new_rows.append(new_row)
            try:
                await callback.message.edit_reply_markup(reply_markup=InlineKeyboardMarkup(inline_keyboard=new_rows))
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"Error in handle_request_tmdb_callback: {e}")
        try:
            await callback.answer("⚠️ So'rov qabul qilinmadi.", show_alert=True)
        except Exception:
            pass
    finally:
        try:
            await callback.answer()
        except Exception:
            pass


@router.callback_query(F.data == "voted_already")
async def handle_already_voted_callback(callback: CallbackQuery):
    try:
        await callback.answer("✅ Siz bu filmga allaqachon ovoz bergansiz!", show_alert=False)
    finally:
        try:
            await callback.answer()
        except Exception:
            pass


@router.message(F.text.in_(["/request", "/sorash", "📥 Kino so'rash", "📥 Buyurtma berish"]))
async def handle_request_command(message: Message):
    base_site = getattr(settings, "WEBSITE_URL", "https://kinochi-project-alpha.vercel.app").rstrip("/")
    await message.answer(
        "🎬 <b>Kino yoki serial qo'shishni so'rash</b>\n\n"
        "O'zingiz qidirgan filmni topa olmadingizmi? TMDB va Kinopoisk orqali butun jahon katalogidan topib, uni bizning bazaga yuklashimizni so'rashingiz mumkin!\n\n"
        f"👉 <b>So'rov yuborish sahifasi:</b>\n{base_site}/requests\n\n"
        "<i>Eng ko'p so'ralgan filmlar birinchi bo'lib platformamizga yuklanadi!</i>",
        parse_mode="HTML"
    )
