import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.database.db import get_user, update_user
from bot.services.weather_api import (
    get_current_weather,
    get_forecast,
    geocode_city,
    reverse_geocode,
)
from bot.services.tone import format_weather
from bot.services.recommendations import clothing_advice, rain_soon_warning
from bot.keyboards.inline import forecast_keyboard
from bot.keyboards.reply import main_menu
from bot.utils.formatters import format_hourly, format_5day

logger = logging.getLogger(__name__)
router = Router()

_ERR_MSG = "❌ Не удалось получить данные о погоде. Попробуйте позже."


async def _resolve_location(message: Message) -> tuple[float, float, str] | None:
    user = await get_user(message.from_user.id)
    if user and user.get("lat") and user.get("lon"):
        return user["lat"], user["lon"], user.get("city", "")
    return None


async def _build_weather_text(lat: float, lon: float, city: str, tone: str) -> str | None:
    w = await get_current_weather(lat, lon)
    if not w:
        return None

    w.city = city or w.city
    text = format_weather(w, tone)

    tips = clothing_advice(w)
    if tips:
        text += "\n\n👕 <b>Рекомендации:</b>\n" + "\n".join(f"  • {t}" for t in tips)

    fc = await get_forecast(lat, lon)
    if fc:
        warning = rain_soon_warning(fc.items)
        if warning:
            text += f"\n\n⚠️ {warning}"

    return text


# ── Геолокация ──────────────────────────────────────────────────────────

@router.message(F.location)
async def on_location(message: Message):
    try:
        lat = message.location.latitude
        lon = message.location.longitude
        city = await reverse_geocode(lat, lon)

        await update_user(message.from_user.id, lat=lat, lon=lon, city=city)

        user = await get_user(message.from_user.id)
        tone = user.get("tone", "neutral") if user else "neutral"

        text = await _build_weather_text(lat, lon, city, tone)
        if not text:
            await message.answer(_ERR_MSG)
            return

        await message.answer(text, parse_mode="HTML", reply_markup=main_menu)
    except Exception as e:
        logger.exception("on_location error: %s", e)
        await message.answer(_ERR_MSG)


# ── Текущая погода (кнопка) ────────────────────────────────────────────

@router.message(F.text == "🌤️ Погода сейчас")
async def current_weather(message: Message):
    try:
        loc = await _resolve_location(message)
        if not loc:
            await message.answer(
                "📍 Сначала отправьте геолокацию или напишите название города.",
                reply_markup=main_menu,
            )
            return

        lat, lon, city = loc
        user = await get_user(message.from_user.id)
        tone = user.get("tone", "neutral") if user else "neutral"

        text = await _build_weather_text(lat, lon, city, tone)
        if not text:
            await message.answer(_ERR_MSG)
            return

        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        logger.exception("current_weather error: %s", e)
        await message.answer(_ERR_MSG)


# ── Что надеть ─────────────────────────────────────────────────────────

@router.message(F.text == "👕 Что надеть")
async def what_to_wear(message: Message):
    try:
        loc = await _resolve_location(message)
        if not loc:
            await message.answer("📍 Сначала укажите город или отправьте геолокацию.")
            return

        lat, lon, city = loc
        w = await get_current_weather(lat, lon)
        if not w:
            await message.answer(_ERR_MSG)
            return

        w.city = city or w.city
        tips = clothing_advice(w)
        text = f"👕 <b>Что надеть — {w.city}</b> ({w.temp:+.0f}°C)\n\n"
        text += "\n".join(f"  • {t}" for t in tips)

        fc = await get_forecast(lat, lon)
        if fc:
            warning = rain_soon_warning(fc.items)
            if warning:
                text += f"\n\n⚠️ {warning}"

        await message.answer(text, parse_mode="HTML")
    except Exception as e:
        logger.exception("what_to_wear error: %s", e)
        await message.answer(_ERR_MSG)


# ── Прогноз ────────────────────────────────────────────────────────────

@router.message(F.text == "📅 Прогноз")
async def forecast_menu(message: Message):
    loc = await _resolve_location(message)
    if not loc:
        await message.answer("📍 Сначала укажите город или отправьте геолокацию.")
        return
    await message.answer("Выберите тип прогноза:", reply_markup=forecast_keyboard())


@router.callback_query(F.data == "forecast:hourly")
async def forecast_hourly(callback: CallbackQuery):
    try:
        user = await get_user(callback.from_user.id)
        if not user or not user.get("lat"):
            await callback.answer("Сначала укажите город", show_alert=True)
            return

        fc = await get_forecast(user["lat"], user["lon"])
        if not fc:
            await callback.answer("Ошибка получения данных", show_alert=True)
            return

        fc.city = user.get("city") or fc.city
        text = format_hourly(fc)
        await callback.message.edit_text(text, parse_mode="HTML")
        await callback.answer()
    except Exception as e:
        logger.exception("forecast_hourly error: %s", e)
        await callback.answer("Ошибка получения данных", show_alert=True)


@router.callback_query(F.data == "forecast:5day")
async def forecast_5day(callback: CallbackQuery):
    try:
        user = await get_user(callback.from_user.id)
        if not user or not user.get("lat"):
            await callback.answer("Сначала укажите город", show_alert=True)
            return

        fc = await get_forecast(user["lat"], user["lon"])
        if not fc:
            await callback.answer("Ошибка получения данных", show_alert=True)
            return

        fc.city = user.get("city") or fc.city
        text = format_5day(fc)
        await callback.message.edit_text(text, parse_mode="HTML")
        await callback.answer()
    except Exception as e:
        logger.exception("forecast_5day error: %s", e)
        await callback.answer("Ошибка получения данных", show_alert=True)


# ── Город по команде /city ─────────────────────────────────────────────

@router.message(F.text.lower().in_({"привет", "здравствуйте", "хай", "hello", "hi", "хелло", "здарова", "прив", "ку"}))
async def on_greeting(message: Message):
    await message.answer(
        "👋 Привет! Используй кнопки меню ниже.\n\n"
        "Чтобы задать город, напиши:\n<code>/city Москва</code>",
        parse_mode="HTML",
        reply_markup=main_menu,
    )


@router.message(F.text.startswith("/city"))
async def cmd_city(message: Message):
    parts = message.text.strip().split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "🏙️ Напишите город после команды.\n"
            "Пример: <code>/city Москва</code>",
            parse_mode="HTML",
        )
        return

    city_name = parts[1].strip()
    try:
        coords = await geocode_city(city_name)
        if not coords:
            await message.answer(
                f"🔍 Город «{city_name}» не найден. Проверьте написание.\n"
                f"Пример: <code>/city Москва</code>",
                parse_mode="HTML",
            )
            return

        lat, lon = coords
        city = city_name.title()
        await update_user(message.from_user.id, lat=lat, lon=lon, city=city)

        user = await get_user(message.from_user.id)
        tone = user.get("tone", "neutral") if user else "neutral"

        result = await _build_weather_text(lat, lon, city, tone)
        if not result:
            await message.answer(
                f"✅ Город <b>{city}</b> сохранён, но данные о погоде временно недоступны.",
                parse_mode="HTML",
                reply_markup=main_menu,
            )
            return

        await message.answer(
            f"✅ Город <b>{city}</b> сохранён!\n\n{result}",
            parse_mode="HTML",
            reply_markup=main_menu,
        )
    except Exception as e:
        logger.exception("cmd_city error: %s", e)
        await message.answer(_ERR_MSG)


# ── Неизвестный текст (fallback) ──────────────────────────────────────

@router.message(F.text & ~F.text.startswith("/"))
async def unknown_text(message: Message):
    text = message.text.strip()

    known_buttons = {
        "🌤️ Погода сейчас", "📅 Прогноз", "👕 Что надеть",
        "🏃 Активности", "🗺️ Погода по пути", "❤️ Здоровье",
        "⚙️ Настройки", "📍 Отправить геолокацию",
        "🕒 Погода на время",
    }
    if text in known_buttons:
        return

    await message.answer(
        "🤔 Не понял. Используй кнопки меню или команды:\n\n"
        "• <code>/city Москва</code> — задать город\n"
        "• <code>/start</code> — начать сначала\n"
        "• 📍 Кнопка геолокации — определить город автоматически",
        parse_mode="HTML",
        reply_markup=main_menu,
    )
