from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

from aiogram.types import WebAppInfo
from config import settings

# WebApp requires HTTPS. If settings has http:// (e.g. localhost), fallback to a valid HTTPS url to prevent bot crash.
web_app_url = settings.WEBSITE_URL
if not web_app_url.startswith("https://"):
    web_app_url = "https://kinochi-project-alpha.onrender.com"

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔍 Kino qidirish"),
            KeyboardButton(text="📂 Katalog")
        ],
        [
            KeyboardButton(text="🎲 Tavsiya kino")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Bo'limni tanlang..."
)

catalog_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🎬 Kinolar"),
            KeyboardButton(text="📺 Seriallar")
        ],
        [
            KeyboardButton(text="🔙 Asosiy menyu")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Nimani ko'ramiz?"
)
