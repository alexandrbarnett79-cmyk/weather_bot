from aiogram import Router, F
from aiogram.types import Message

from bot.database.db import get_user
from bot.services.weather_api import get_current_weather
from bot.services.recommendations import health_advice, HEALTH_MODES
from bot.keyboards.inline import health_keyboard

router = Router()


@router.message(F.text == "❤️ Здоровье")
async def show_health(message: Message):
    user = await get_user(message.from_user.id)
    if not user or not user.get("lat"):
        await message.answer("📍 Сначала укажите город или отправьте геолокацию.")
        return

    mode = user.get("health_mode", "")
    if not mode:
        await message.answer(
            "❤️ <b>Профиль здоровья не настроен.</b>\n\nВыберите свой профиль:",
            parse_mode="HTML",
            reply_markup=health_keyboard(),
        )
        return

    w = await get_current_weather(user["lat"], user["lon"])
    if not w:
        await message.answer("❌ Не удалось получить данные о погоде.")
        return

    w.city = user.get("city") or w.city
    tips = health_advice(mode, w)
    label = HEALTH_MODES.get(mode, mode)

    pressure_mmhg = round(w.pressure * 0.750062)

    text = (
        f"❤️ <b>Здоровье и самочувствие — {w.city}</b>\n"
        f"Профиль: {label}\n\n"
        f"🌡️ Температура: {w.temp:+.0f}°C (ощущается {w.feels_like:+.0f}°C)\n"
        f"📊 Давление: {pressure_mmhg} мм рт. ст.\n"
        f"💧 Влажность: {w.humidity}%\n\n"
        f"<b>Рекомендации:</b>\n"
    )
    text += "\n".join(f"  • {t}" for t in tips)

    await message.answer(text, parse_mode="HTML")
