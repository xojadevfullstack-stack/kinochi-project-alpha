import logging
import html
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from services.api_client import api_client
from config import settings

logger = logging.getLogger(__name__)

router = Router()


async def render_user_profile(user_id: int, first_name: str, username: str = None):
    # Ensure user is registered
    try:
        await api_client.register_user(
            telegram_id=user_id,
            username=username,
            first_name=first_name,
            last_name=None
        )
    except Exception as e:
        logger.warning(f"Error ensuring user registration in profile: {e}")

    summary = await api_client.get_user_summary(user_id)
    if not summary:
        text = (
            f"👤 <b>Foydalanuvchi Profili</b>\n\n"
            f"🆔 Telegram ID: <code>{user_id}</code>\n"
            f"👤 Ism: <b>{html.escape(first_name)}</b>\n\n"
            f"ℹ️ Sizning faollik tarixingiz hali shakllanmagan. Kino yoki serial tomosha qilib profilingizni boyiting!"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="🎲 Tavsiyalar", callback_data="menu_random")
        builder.button(text="🔙 Asosiy menyu", callback_data="menu_main")
        builder.adjust(1)
        return text, builder.as_markup()

    u_data = summary.get("user", {})
    total_watched = summary.get("total_watched", 0)
    achievements = summary.get("achievements", [])
    subscriptions = summary.get("subscriptions", [])
    recent_history = summary.get("recent_history", [])

    join_date = u_data.get("joined_at", "")
    if join_date:
        join_date = join_date.split("T")[0]

    lines = [
        "👤 <b>Foydalanuvchi Profili</b>\n",
        f"🆔 ID: <code>{user_id}</code>",
        f"👤 Ism: <b>{html.escape(u_data.get('first_name') or first_name)}</b>",
    ]
    if u_data.get("username"):
        lines.append(f"🔗 Username: @{html.escape(u_data['username'])}")
    if join_date:
        lines.append(f"📅 A'zo bo'lgan: {join_date}")

    lines.append(f"\n👁 <b>Tomosha faolligi:</b> <b>{total_watched} ta</b> film/qism")

    # Achievements
    lines.append("\n🏆 <b>Yutuqlar (Achievements):</b>")
    if achievements:
        for ach in achievements[:4]:
            lines.append(f"  • 🎖 {html.escape(ach.get('title', 'Yutuq'))}")
        if len(achievements) > 4:
            lines.append(f"  <i>...va yana {len(achievements) - 4} ta</i>")
    else:
        lines.append("  <i>Hali yutuqlar yo'q. Ko'proq tomosha qiling!</i>")

    # Subscriptions
    col_subs = summary.get("collection_subscriptions", [])
    lines.append("\n🔔 <b>Faol Serial Obunalari:</b>")
    if subscriptions:
        for sub in subscriptions[:3]:
            lines.append(f"  • 📺 {html.escape(sub.get('title', 'Serial'))}")
        if len(subscriptions) > 3:
            lines.append(f"  <i>...va yana {len(subscriptions) - 3} ta</i>")
    else:
        lines.append("  <i>Hozircha hech qaysi serialga obuna emassiz.</i>")

    lines.append("\n🎬 <b>Franshiza va To'plam Obunalari:</b>")
    if col_subs:
        for csub in col_subs[:3]:
            lines.append(f"  • 📂 {html.escape(csub.get('name', 'To\'plam'))}")
        if len(col_subs) > 3:
            lines.append(f"  <i>...va yana {len(col_subs) - 3} ta</i>")
    else:
        lines.append("  <i>Hozircha hech qanday franshizaga obuna emassiz.</i>")

    # Recent history
    if recent_history:
        lines.append("\n🎞 <b>So'nggi tomoshalar:</b>")
        for h in recent_history[:3]:
            lines.append(f"  • {html.escape(h.get('title', 'Noma\'lum'))}")

    text = "\n".join(lines)

    builder = InlineKeyboardBuilder()
    builder.button(text="✨ Didga mos tavsiyalar", callback_data="rec_cat:personalized:0")
    if subscriptions or summary.get("collection_subscriptions"):
        builder.button(text="🔔 Obunalarni boshqarish", callback_data="manage_my_subs")

    # Website magic login button
    try:
        base_site = getattr(settings, "WEBSITE_URL", "https://kinochi-project-alpha.vercel.app").rstrip("/")
        if not base_site or "localhost" in base_site or "127.0.0.1" in base_site:
            base_site = "https://kinochi-project-alpha.vercel.app"
        token = await api_client.generate_login_token(telegram_id=user_id, first_name=first_name, username=username)
        if token:
            builder.button(text="🌐 Saytdagi Shaxsiy Kabinet", web_app=WebAppInfo(url=f"{base_site}/?auth_token={token}"))
    except Exception as e:
        logger.warning(f"Error generating web login button in profile: {e}")

    builder.button(text="🔙 Asosiy menyu", callback_data="menu_main")
    builder.adjust(1)

    return text, builder.as_markup()


@router.callback_query(F.data == "menu_profile")
async def handle_profile_callback(callback: CallbackQuery):
    try:
        text, markup = await render_user_profile(
            user_id=callback.from_user.id,
            first_name=callback.from_user.first_name,
            username=callback.from_user.username
        )
        try:
            if callback.message.photo or callback.message.video:
                await callback.message.delete()
                await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
            else:
                await callback.message.edit_text(text, parse_mode="HTML", reply_markup=markup)
        except Exception:
            await callback.message.answer(text, parse_mode="HTML", reply_markup=markup)
    finally:
        try:
            await callback.answer()
        except Exception:
            pass


@router.message(Command("profile"))
async def handle_profile_command(message: Message):
    text, markup = await render_user_profile(
        user_id=message.from_user.id,
        first_name=message.from_user.first_name,
        username=message.from_user.username
    )
    await message.answer(text, parse_mode="HTML", reply_markup=markup)



@router.callback_query(F.data == "manage_my_subs")
async def handle_manage_my_subs(callback: CallbackQuery):
    try:
        summary = await api_client.get_user_summary(callback.from_user.id)
        if not summary:
            await callback.answer("Obunalar topilmadi", show_alert=True)
            return

        series_subs = summary.get("subscriptions", [])
        col_subs = summary.get("collection_subscriptions", [])

        if not series_subs and not col_subs:
            await callback.answer("Sizda hozircha hech qanday faol obuna yo'q.", show_alert=True)
            return

        text = "🔔 <b>Mening Obunalarim</b>\n\nYangi qismlar yoki filmlar chiqqanda bot sizga avtomatik xabar beradi. Obunani o'chirish uchun yonidagi tugmani bosing:\n"

        builder = InlineKeyboardBuilder()
        for s in series_subs:
            s_title = s.get("title", "Serial")[:20]
            s_id = s.get("series_id")
            builder.button(text=f"📺 {s_title}", callback_data=f"series_info:{s_id}")
            builder.button(text="❌ O'chirish", callback_data=f"prof_unsub_ser_{s_id}")

        for c in col_subs:
            c_name = c.get("name", "To'plam")[:20]
            col_id = c.get("collection_id")
            builder.button(text=f"📂 {c_name}", callback_data=f"col_view_{col_id}")
            builder.button(text="❌ O'chirish", callback_data=f"prof_unsub_col_{col_id}")

        builder.button(text="🔙 Profilga qaytish", callback_data="menu_profile")
        builder.adjust(2, 2, 1)

        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=builder.as_markup())
    except Exception as e:
        logger.warning(f"Error in handle_manage_my_subs: {e}")
    finally:
        try:
            await callback.answer()
        except Exception:
            pass


@router.callback_query(F.data.startswith("prof_unsub_col_"))
async def handle_prof_unsub_col(callback: CallbackQuery):
    try:
        col_id = int(callback.data.split("_", 3)[3])
        await api_client.toggle_collection_subscription(col_id, callback.from_user.id)
        await callback.answer("🔕 Franshiza obunasi bekor qilindi.", show_alert=True)
        # Re-render manage subscriptions list
        await handle_manage_my_subs(callback)
    except Exception as e:
        logger.warning(f"Error in handle_prof_unsub_col: {e}")
    finally:
        try:
            await callback.answer()
        except Exception:
            pass


@router.callback_query(F.data.startswith("prof_unsub_ser_"))
async def handle_prof_unsub_ser(callback: CallbackQuery):
    try:
        series_id = int(callback.data.split("_", 3)[3])
        await api_client.toggle_series_subscription(series_id, callback.from_user.id)
        await callback.answer("🔕 Serial obunasi bekor qilindi.", show_alert=True)
        # Re-render manage subscriptions list
        await handle_manage_my_subs(callback)
    except Exception as e:
        logger.warning(f"Error in handle_prof_unsub_ser: {e}")
    finally:
        try:
            await callback.answer()
        except Exception:
            pass
