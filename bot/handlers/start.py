from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.database.db import upsert_user
from bot.keyboards.reply import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message):
    await upsert_user(message.from_user.id, message.from_user.username)
    await message.answer(
        "👋 <b>Привет!</b> Я — твой персональный помощник по погоде.\n\n"
        "<b>Как начать:</b>\n"
        "1️⃣ Нажми 📍 <b>Отправить геолокацию</b> — я определю город автоматически\n"
        "2️⃣ Или напиши команду: <code>/city Москва</code>\n\n"
        "<b>Что я умею:</b>\n"
        "• 🌤️ Текущая погода и прогноз\n"
        "• 👕 Рекомендации, что надеть\n"
        "• 🏃 Подсказки для активностей\n"
        "• 🗺️ Погода по маршруту\n"
        "• ❤️ Учёт самочувствия\n"
        "• 🎭 7 тональностей подачи\n\n"
        "⬇️ Используй кнопки меню ниже!",
        reply_markup=main_menu,
        parse_mode="HTML",
    )
