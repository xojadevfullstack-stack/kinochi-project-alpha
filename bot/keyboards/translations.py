from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def format_quality_label(raw_lang: str) -> str:
    """Formats translation/quality label with clean icons."""
    lang = (raw_lang or "O'zbekcha").strip()
    l_lower = lang.lower()
    if "4k" in l_lower or "2160" in l_lower or "uhd" in l_lower:
        return f"💎 {lang}"
    elif "1080" in l_lower or "fhd" in l_lower:
        return f"🍿 {lang}"
    elif "720" in l_lower or "hd" in l_lower:
        return f"🎬 {lang}"
    elif "480" in l_lower or "sd" in l_lower:
        return f"📱 {lang}"
    elif "360" in l_lower:
        return f"⚡ {lang}"
    return f"🎙 {lang}"

def get_translations_keyboard(item_type: str, item_code: str, translations: list) -> InlineKeyboardMarkup:
    """
    Builds a keyboard to select a translation/quality/studio.
    item_type is either 'M' for Movie or 'E' for Episode.
    callback_data format: tr_<type>_<code>_<translation_id>
    """
    builder = InlineKeyboardBuilder()
    
    for t in translations:
        label = format_quality_label(t.get("language", "O'zbekcha"))
        builder.button(
            text=label,
            callback_data=f"tr_{item_type}_{item_code}_{t['id']}"
        )
        
    builder.adjust(1) # One button per row
    return builder.as_markup()
