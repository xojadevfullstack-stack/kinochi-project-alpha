from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_translations_keyboard(item_type: str, item_code: str, translations: list) -> InlineKeyboardMarkup:
    """
    Builds a keyboard to select a translation/studio.
    item_type is either 'M' for Movie or 'E' for Episode.
    callback_data format: tr_<type>_<code>_<translation_id>
    """
    builder = InlineKeyboardBuilder()
    
    for t in translations:
        builder.button(
            text=t.get("language", "Asosiy"),
            callback_data=f"tr_{item_type}_{item_code}_{t['id']}"
        )
        
    builder.adjust(1) # One button per row
    return builder.as_markup()
