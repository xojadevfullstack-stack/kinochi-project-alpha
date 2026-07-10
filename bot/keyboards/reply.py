from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="🔍 Kino qidirish"),
            KeyboardButton(text="🎲 Tavsiya kino")
        ],
        [
            KeyboardButton(text="🌐 Saytga o'tish")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Bo'limni tanlang..."
)
