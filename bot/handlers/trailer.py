import re
import logging
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from services.api_client import api_client

logger = logging.getLogger(__name__)
router = Router()

async def send_trailer(bot: Bot, chat_id: int, trailer_url: str):
    """Sends the trailer based on its type."""
    
    # 1. YouTube link
    if "youtube.com" in trailer_url or "youtu.be" in trailer_url:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="▶️ YouTube'da ko'rish", url=trailer_url)
        ]])
        await bot.send_message(
            chat_id=chat_id,
            text=f"🎬 <b>Treyler:</b>\n{trailer_url}",
            reply_markup=kb,
            parse_mode="HTML"
        )
        return
        
    # 2. Telegram link
    tg_domain_match = re.search(r'(?:t\.me|telegram\.me|telegram\.dog)/([^\s?#]+)', trailer_url)
    if tg_domain_match:
        path = tg_domain_match.group(1).strip('/')
        parts = [p for p in path.split('/') if p]
        is_private = (parts[0] == 'c')
        
        from_chat_id = None
        message_id = None
        
        if is_private and len(parts) >= 3 and parts[1].isdigit() and parts[-1].isdigit():
            chat_identifier = parts[1]
            from_chat_id = f"-100{chat_identifier}"
            message_id = int(parts[-1])
        elif not is_private and len(parts) >= 2 and parts[-1].isdigit():
            chat_identifier = parts[0]
            from_chat_id = chat_identifier if (chat_identifier.isdigit() or chat_identifier.startswith('-')) else f"@{chat_identifier}"
            message_id = int(parts[-1])
            
        if from_chat_id and message_id:
            try:
                await bot.copy_message(
                    chat_id=chat_id,
                    from_chat_id=from_chat_id,
                    message_id=message_id
                )
            except (TelegramBadRequest, TelegramForbiddenError) as e:
                logger.warning(f"Failed to copy trailer from {from_chat_id} (msg {message_id}): {e}")
                await bot.send_message(
                    chat_id=chat_id,
                    text="⚠️ <b>Treyler hozircha mavjud emas</b> yoki unga kirish huquqi yo'q.",
                    parse_mode="HTML"
                )
            return
        
    # 3. MP4 Direct link
    if trailer_url.endswith(".mp4") or "http" in trailer_url:
        try:
            await bot.send_video(
                chat_id=chat_id,
                video=trailer_url,
                caption="🎬 <b>Treyler</b>",
                parse_mode="HTML"
            )
        except TelegramBadRequest as e:
            logger.warning(f"Failed to send MP4 trailer {trailer_url}: {e}")
            await bot.send_message(
                chat_id=chat_id,
                text="⚠️ <b>Treylerni yuklashda xatolik yuz berdi.</b>",
                parse_mode="HTML"
            )
        return

@router.callback_query(F.data.startswith("trailer_m_"))
async def handle_movie_trailer(callback: CallbackQuery):
    code = callback.data.split("_", 2)[2]
    await callback.answer()
    
    movie = await api_client.get_movie_by_code(code)
    if not movie or not movie.get("trailer_url"):
        await callback.message.answer("⚠️ Treyler topilmadi.", show_alert=True)
        return
        
    await send_trailer(callback.bot, callback.from_user.id, movie["trailer_url"])

@router.callback_query(F.data.startswith("trailer_s_"))
async def handle_series_trailer(callback: CallbackQuery):
    series_id_str = callback.data.split("_", 2)[2]
    await callback.answer()
    
    try:
        series_id = int(series_id_str)
        series = await api_client.get_series_by_id(series_id)
        if not series or not series.get("trailer_url"):
            await callback.message.answer("⚠️ Treyler topilmadi.", show_alert=True)
            return
            
        await send_trailer(callback.bot, callback.from_user.id, series["trailer_url"])
    except ValueError:
        await callback.message.answer("⚠️ Xatolik.", show_alert=True)
