from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🎬 Katalog"),
            KeyboardButton(text="🔍 Qidirish")
        ],
        [
            KeyboardButton(text="🌐 Saytga o'tish")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Kerakli bo'limni tanlang..."
)
