import logging
import random
import html
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.api_client import api_client

logger = logging.getLogger(__name__)

router = Router()

@router.callback_query(F.data == "menu_random")
async def handle_recommendation_menu(callback: CallbackQuery):
    text = (
        "🎲 <b>Tavsiya Bo'limi</b>\n\n"
        "Qaysi yo'nalish bo'yicha film yoki serial tavsiya qilaylik?"
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="🎬 Kinolar", callback_data="rec_cat:movie:0")
    builder.button(text="📺 Seriallar", callback_data="rec_cat:series:0")
    
    # Dynamic active pages (Anime, Doramalar, Multfilm va boshqalar)
    try:
        pages_data = await api_client.get_pages()
        for p in pages_data.get("items", []):
            if p.get("is_active"):
                title = p.get("title", "")
                pid = p.get("id")
                icon = "📂"
                t_low = title.lower()
                if "anime" in t_low:
                    icon = "🎌"
                elif "dorama" in t_low:
                    icon = "🎭"
                elif "mult" in t_low:
                    icon = "🧸"
                builder.button(text=f"{icon} {title}", callback_data=f"rec_cat:page_{pid}:0")
    except Exception as e:
        logger.error(f"Error loading pages in recommendation: {e}")

    builder.button(text="🎲 Har qanday (Random)", callback_data="rec_cat:any:0")
    builder.button(text="🔙 Asosiy menyu", callback_data="menu_main")
    builder.adjust(2)

    try:
        if callback.message.photo or callback.message.video:
            await callback.message.delete()
            await callback.message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
        else:
            await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    except Exception:
        await callback.message.answer(text, parse_mode="HTML", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data.startswith("rec_cat:"))
async def handle_get_recommendation(callback: CallbackQuery):
    parts = callback.data.split(":")
    cat_type = parts[1]
    skip = int(parts[2]) if len(parts) > 2 else 0

    item = None
    item_type = "movie"

    try:
        if cat_type == "movie":
            data = await api_client.get_movies(skip=skip, limit=1)
            items = data.get("items", [])
            if not items and skip > 0:
                data = await api_client.get_movies(skip=0, limit=1)
                items = data.get("items", [])
                skip = 0
            if items:
                item = items[0]
                item_type = "movie"

        elif cat_type == "series":
            data = await api_client.get_series(skip=skip, limit=1)
            items = data.get("items", [])
            if not items and skip > 0:
                data = await api_client.get_series(skip=0, limit=1)
                items = data.get("items", [])
                skip = 0
            if items:
                item = items[0]
                item_type = "series"

        elif cat_type.startswith("page_"):
            page_id = int(cat_type.replace("page_", ""))
            m_data = await api_client.get_movies(limit=20, page_id=page_id)
            s_data = await api_client.get_series(limit=20, page_id=page_id)
            all_page_items = []
            for m in m_data.get("items", []):
                m["_item_type"] = "movie"
                all_page_items.append(m)
            for s in s_data.get("items", []):
                s["_item_type"] = "series"
                all_page_items.append(s)

            if all_page_items:
                idx = skip % len(all_page_items)
                item = all_page_items[idx]
                item_type = item.get("_item_type", "movie")

        elif cat_type == "any":
            choice = random.choice(["movie", "series"])
            if choice == "movie":
                data = await api_client.get_movies(limit=15)
                items = data.get("items", [])
                if items:
                    item = random.choice(items)
                    item_type = "movie"
            else:
                data = await api_client.get_series(limit=15)
                items = data.get("items", [])
                if items:
                    item = random.choice(items)
                    item_type = "series"
    except Exception as e:
        logger.error(f"Error fetching recommendation: {e}")

    if not item:
        await callback.answer("Afsuski, ushbu toifada hozircha tavsiyalar yo'q.", show_alert=True)
        return

    title = html.escape(item.get("title", "Noma'lum"))
    rating = item.get("imdb_rating") or item.get("tmdb_rating") or "N/A"

    # Safely format genres (prevent character-by-character string splitting)
    raw_genres = item.get("genres")
    if isinstance(raw_genres, list):
        genres = ", ".join(str(g).strip() for g in raw_genres if g and str(g).strip())
    elif isinstance(raw_genres, str) and raw_genres.strip():
        cleaned = [g.strip() for g in raw_genres.split(",") if g.strip()]
        genres = ", ".join(cleaned) if cleaned else raw_genres.strip()
    elif item.get("categories"):
        cats = item.get("categories")
        if isinstance(cats, list):
            genres = ", ".join(c.get("name", "") if isinstance(c, dict) else str(c) for c in cats)
        else:
            genres = str(cats)
    else:
        genres = "Umumiy"

    desc = html.escape(item.get("description") or "Tavsif mavjud emas.")
    if len(desc) > 350:
        desc = desc[:347] + "..."

    type_name = "🎬 <b>Film:</b>" if item_type == "movie" else "📺 <b>Serial:</b>"
    
    caption_lines = [
        "🎲 <b>Siz uchun tavsiya:</b>\n",
        f"{type_name} <b>{title}</b>",
    ]
    
    year = item.get("release_year")
    if year:
        caption_lines.append(f"📅 <b>Yil:</b> {year}")
        
    if rating and str(rating) != "N/A":
        caption_lines.append(f"⭐️ <b>Reyting:</b> {rating}")
        
    caption_lines.append(f"🎭 <b>Janr:</b> {genres}")
    
    if desc and desc != "Tavsif mavjud emas.":
        caption_lines.append(f"\n📝 <b>Tavsif:</b>\n<i>{desc}</i>")
        
    caption = "\n".join(caption_lines)

    builder = InlineKeyboardBuilder()
    if item_type == "movie":
        code = item.get("code")
        builder.button(text="🍿 Tomosha qilish", callback_data=f"movie_{code}")
    else:
        sid = item.get("id")
        builder.button(text="🍿 Fasllarni ko'rish", callback_data=f"search_series_{sid}")

    builder.button(text="🔄 Keyingi tavsiya", callback_data=f"rec_cat:{cat_type}:{skip + 1}")
    builder.button(text="🔙 Boshqa toifa", callback_data="menu_random")
    builder.adjust(1, 2)

    poster_url = item.get("poster_url")
    try:
        if poster_url and poster_url.startswith("http"):
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.bot.send_photo(
                chat_id=callback.from_user.id,
                photo=poster_url,
                caption=caption,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        else:
            if callback.message.photo:
                await callback.message.delete()
                await callback.message.answer(caption, parse_mode="HTML", reply_markup=builder.as_markup())
            else:
                await callback.message.edit_text(caption, parse_mode="HTML", reply_markup=builder.as_markup())
    except Exception as e:
        logger.warning(f"Failed to send recommendation: {e}")
        await callback.message.answer(caption, parse_mode="HTML", reply_markup=builder.as_markup())

    await callback.answer()
