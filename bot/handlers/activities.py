from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.database.db import get_user
from bot.services.weather_api import get_current_weather
from bot.services.recommendations import activity_advice, ACTIVITIES
from bot.keyboards.inline import activities_keyboard

router = Router()


@router.message(F.text == "🏃 Активности")
async def show_activities(message: Message):
    user = await get_user(message.from_user.id)
    if not user or not user.get("lat"):
        await message.answer("📍 Сначала укажите город или отправьте геолокацию.")
        return

    await message.answer(
        "🏃 <b>Выберите активность:</b>",
        parse_mode="HTML",
        reply_markup=activities_keyboard(),
    )


@router.callback_query(F.data.startswith("activity:"))
async def on_activity(callback: CallbackQuery):
    activity = callback.data.split(":")[1]
    user = await get_user(callback.from_user.id)
    if not user or not user.get("lat"):
        await callback.answer("Сначала укажите город", show_alert=True)
        return

    w = await get_current_weather(user["lat"], user["lon"])
    if not w:
        await callback.answer("Ошибка получения данных", show_alert=True)
        return

    w.city = user.get("city") or w.city
    label = ACTIVITIES.get(activity, activity)
    advice = activity_advice(activity, w)

    text = (
        f"{label}\n"
        f"📍 {w.city} | {w.temp:+.0f}°C, {w.description}\n\n"
        f"{advice}"
    )
    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()
