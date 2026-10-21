from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from services.api_client import api_client
from utils.info_sender import send_movie_info, send_series_info
from keyboards.inline import get_main_menu_inline, get_catalog_categories_inline, build_catalog_items_list, build_page_items_list
from config import settings
import logging

logger = logging.getLogger(__name__)

router = Router()

def get_webapp_url():
    base = getattr(settings, "WEBSITE_URL", "https://kinochi-project-alpha.vercel.app/").rstrip("/")
    return f"{base}/"

async def send_catalog(target: CallbackQuery | Message, state: FSMContext = None):
    """Holatdan qat'iy nazar katalogni chiqaradi va kerak bo'lsa FSM holatini tozalaydi."""
    if state:
        await state.clear()
        
    text = "📂 <b>Katalog</b>\n\nQuyidagi toifalardan birini tanlang:"
    
    try:
        pages_data = await api_client.get_pages()
        pages = pages_data.get("items", [])
    except Exception as e:
        logger.warning(f"Error fetching pages for catalog: {e}")
        pages = []
    
    markup = get_catalog_categories_inline(pages)
    
    if isinstance(target, CallbackQuery) or hasattr(target, "message"):
        msg = target.message
        try:
            if msg.photo or msg.video:
                try:
                    await msg.delete()
                except Exception:
                    pass
                await msg.answer(text, parse_mode="HTML", reply_markup=markup)
            else:
                try:
                    await msg.edit_text(text, parse_mode="HTML", reply_markup=markup)
                except Exception:
                    await msg.answer(text, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            logger.warning(f"Error in send_catalog via callback: {e}")
            await msg.answer(text, parse_mode="HTML", reply_markup=markup)
    else:
        await target.answer(text, parse_mode="HTML", reply_markup=markup)

@router.callback_query(F.data == "catalog_collections")
async def handle_catalog_collections(callback: CallbackQuery):
    try:
        collections = await api_client.get_collections()
        if not collections:
            await callback.answer("Hozircha faol to'plamlar mavjud emas.", show_alert=True)
            return

        text = (
            "📚 <b>Kino To'plamlari va Franshizalar</b>\n\n"
            "O'zingizga yoqqan kino olamini tanlang, barcha qismlarini xronologik tartibda tomosha qiling va yangi qismlariga obuna bo'ling!"
        )

        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        for col in collections:
            c_name = col.get("name", "To'plam")
            count = col.get("items_count", 0)
            is_f = col.get("is_franchise", True)
            icon = "🎬" if is_f else "📂"
            count_str = f" ({count} ta)" if count > 0 else ""
            builder.button(
                text=f"{icon} {c_name}{count_str}",
                callback_data=f"col_view_{col.get('id')}"
            )

        builder.button(text="🔙 Katalogga qaytish", callback_data="menu_catalog")
        builder.adjust(1)

        try:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
        except Exception:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
    except Exception as e:
        logger.warning(f"Error in handle_catalog_collections: {e}")
    finally:
        try:
            await callback.answer()
        except Exception:
            pass


@router.callback_query(F.data == "menu_catalog")
async def handle_catalog_btn(callback: CallbackQuery, state: FSMContext = None):
    try:
        await send_catalog(callback, state)
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

@router.message(F.text.lower().in_(["katalog", "📂 katalog", "ortga", "◀️ ortga", "orqaga", "/katalog", "/catalog"]))
async def handle_catalog_message(message: Message, state: FSMContext = None):
    await send_catalog(message, state)

@router.callback_query(F.data == "menu_main")
async def handle_back_to_main(callback: CallbackQuery):
    try:
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
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

import math

@router.callback_query(F.data == "cat_noop")
async def handle_catalog_noop(callback: CallbackQuery):
    try:
        pass
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

@router.callback_query(F.data.startswith("cat_info:"))
async def handle_catalog_info(callback: CallbackQuery):
    try:
        parts = callback.data.split(":")
        if len(parts) >= 4:
            page, total_pages, total = parts[1], parts[2], parts[3]
            await callback.answer(f"📄 Sahifa {page} / {total_pages}\n📊 Jami: {total} ta", show_alert=True)
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

@router.callback_query(F.data == "catalog_all_movies")
@router.callback_query(F.data.startswith("cat_movies:"))
async def handle_catalog_all_movies(callback: CallbackQuery):
    try:
        page = 1
        if callback.data.startswith("cat_movies:"):
            try:
                page = max(1, int(callback.data.split(":")[1]))
            except ValueError:
                page = 1

        limit = 10
        skip = (page - 1) * limit
        movies_data = await api_client.get_movies(skip=skip, limit=limit)
        items = movies_data.get("items", [])
        total = movies_data.get("total", 0)

        if not items and page > 1:
            page = 1
            skip = 0
            movies_data = await api_client.get_movies(skip=skip, limit=limit)
            items = movies_data.get("items", [])
            total = movies_data.get("total", 0)

        if not items:
            await callback.answer("Hozircha kinolar mavjud emas.", show_alert=True)
            return

        total_pages = max(1, math.ceil(total / limit)) if total > 0 else 1
        text = (
            f"🎬 <b>Kinolar ro'yxati</b> (Sahifa {page}/{total_pages})\n"
            f"<i>Jami: {total} ta kino. Quyidagilardan birini tanlang:</i>"
        )
        markup = build_catalog_items_list(items, "movie", page=page, total=total, page_size=limit)
        try:
            if callback.message.photo or callback.message.video:
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
            else:
                try:
                    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
                except Exception:
                    await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            logger.warning(f"Error in handle_catalog_all_movies: {e}")
            await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

@router.callback_query(F.data == "catalog_all_series")
@router.callback_query(F.data.startswith("cat_series:"))
async def handle_catalog_all_series(callback: CallbackQuery):
    try:
        page = 1
        if callback.data.startswith("cat_series:"):
            try:
                page = max(1, int(callback.data.split(":")[1]))
            except ValueError:
                page = 1

        limit = 10
        skip = (page - 1) * limit
        series_data = await api_client.get_series(skip=skip, limit=limit)
        items = series_data.get("items", [])
        total = series_data.get("total", 0)

        if not items and page > 1:
            page = 1
            skip = 0
            series_data = await api_client.get_series(skip=skip, limit=limit)
            items = series_data.get("items", [])
            total = series_data.get("total", 0)

        if not items:
            await callback.answer("Hozircha seriallar mavjud emas.", show_alert=True)
            return

        total_pages = max(1, math.ceil(total / limit)) if total > 0 else 1
        text = (
            f"📺 <b>Seriallar ro'yxati</b> (Sahifa {page}/{total_pages})\n"
            f"<i>Jami: {total} ta serial. Quyidagilardan birini tanlang:</i>"
        )
        markup = build_catalog_items_list(items, "series", page=page, total=total, page_size=limit)
        try:
            if callback.message.photo or callback.message.video:
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
            else:
                try:
                    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
                except Exception:
                    await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            logger.warning(f"Error in handle_catalog_all_series: {e}")
            await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

@router.callback_query(F.data.startswith("menu_page_"))
@router.callback_query(F.data.startswith("cat_dyn:"))
async def handle_page_catalog(callback: CallbackQuery):
    try:
        page = 1
        if callback.data.startswith("cat_dyn:"):
            parts = callback.data.split(":")
            page_id = int(parts[1])
            page = max(1, int(parts[2])) if len(parts) > 2 else 1
        else:
            page_id = int(callback.data.split("_")[-1])

        limit = 10
        skip = (page - 1) * limit

        # Fetch movies and series for this page
        movies_data = await api_client.get_movies(skip=skip, limit=limit, page_id=page_id)
        series_data = await api_client.get_series(skip=skip, limit=limit, page_id=page_id)
        
        results = []
        for m in movies_data.get("items", []):
            m["type"] = "movie"
            results.append(m)
        for s in series_data.get("items", []):
            s["type"] = "series"
            results.append(s)

        total = (movies_data.get("total") or 0) + (series_data.get("total") or 0)
            
        if not results and page > 1:
            page = 1
            skip = 0
            movies_data = await api_client.get_movies(skip=skip, limit=limit, page_id=page_id)
            series_data = await api_client.get_series(skip=skip, limit=limit, page_id=page_id)
            results = []
            for m in movies_data.get("items", []):
                m["type"] = "movie"
                results.append(m)
            for s in series_data.get("items", []):
                s["type"] = "series"
                results.append(s)
            total = (movies_data.get("total") or 0) + (series_data.get("total") or 0)

        if not results:
            await callback.answer("Hozircha ushbu sahifada hech narsa yo'q.", show_alert=True)
            return

        total_pages = max(1, math.ceil(total / limit)) if total > 0 else 1
        text = (
            f"📂 <b>Sahifa natijalari</b> (Sahifa {page}/{total_pages})\n"
            f"<i>Jami: {total} ta material. Quyidagilardan birini tanlang:</i>"
        )
        markup = build_page_items_list(results, page_id=page_id, page=page, total=total, page_size=limit)
        try:
            if callback.message.photo or callback.message.video:
                try:
                    await callback.message.delete()
                except Exception:
                    pass
                await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
            else:
                try:
                    await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
                except Exception:
                    await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            logger.warning(f"Error in handle_page_catalog: {e}")
            await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

@router.callback_query(F.data.startswith("catalog_item_movie_"))
async def handle_catalog_movie_select(callback: CallbackQuery):
    try:
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
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

@router.callback_query(F.data.startswith("catalog_item_series_"))
async def handle_catalog_series_select(callback: CallbackQuery):
    try:
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
    finally:
        try:
            await callback.answer()
        except Exception:
            pass

@router.callback_query(F.data == "help_search")
async def handle_help_search(callback: CallbackQuery):
    try:
        await callback.answer("Shunchaki chatga kino yoki serial nomini yozib yuboring!", show_alert=True)
    finally:
        try:
            await callback.answer()
        except Exception:
            pass
