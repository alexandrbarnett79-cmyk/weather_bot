from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🌤️ Погода сейчас"), KeyboardButton(text="📅 Прогноз")],
        [KeyboardButton(text="🕒 Погода на время"), KeyboardButton(text="👕 Что надеть")],
        [KeyboardButton(text="🏃 Активности"), KeyboardButton(text="🗺️ Погода по пути")],
        [KeyboardButton(text="❤️ Здоровье"), KeyboardButton(text="⚙️ Настройки")],
        [KeyboardButton(text="📍 Отправить геолокацию", request_location=True)],
    ],
    resize_keyboard=True,
)
