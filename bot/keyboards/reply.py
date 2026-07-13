from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from aiogram.types import WebAppInfo
from config import settings

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔍 Kino qidirish"),
            KeyboardButton(text="📂 Katalog", web_app=WebAppInfo(url=settings.WEBSITE_URL))
        ],
        [
            KeyboardButton(text="🎲 Tavsiya kino"),
            KeyboardButton(text="🌐 Saytga o'tish")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Bo'limni tanlang..."
)
