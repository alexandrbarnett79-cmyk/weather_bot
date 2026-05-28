"""Погода в конкретном месте на конкретное время.

Пользователь вводит: «Москва, завтра 18:30» или просто «через 3 часа»
(во втором случае используется сохранённый город).
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from bot.database.db import get_user
from bot.keyboards.reply import main_menu
from bot.services.weather_api import (
    ForecastItem,
    geocode_city,
    get_forecast,
    interpolate_forecast,
    wind_direction,
)
from bot.utils.time_parser import parse_user_time

logger = logging.getLogger(__name__)
router = Router()

BUTTON_TEXT = "🕒 Погода на время"

_HELP = (
    "🕒 <b>Погода на конкретное время</b>\n\n"
    "Напишите <b>место и время</b> через запятую.\n\n"
    "Примеры:\n"
    "• <code>Москва, завтра 18:30</code>\n"
    "• <code>Сочи, 12.04 09:00</code>\n"
    "• <code>Казань, послезавтра вечером</code>\n"
    "• <code>через 3 часа</code> — для сохранённого города\n"
    "• <code>завтра в 7</code> — тоже по сохранённому городу\n\n"
    "Прогноз доступен на ближайшие <b>5 дней</b>.\n"
    "Отмена — /cancel"
)

_WEEKDAYS_RU = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]


class WhenStates(StatesGroup):
    waiting_input = State()


@router.message(F.text == BUTTON_TEXT)
async def ask_when(message: Message, state: FSMContext):
    await message.answer(_HELP, parse_mode="HTML")
    await state.set_state(WhenStates.waiting_input)


@router.message(Command("cancel"), WhenStates.waiting_input)
async def cancel_when(message: Message, state: FSMContext):
    await state.clear()
    await message.answer("Отменено.", reply_markup=main_menu)


@router.message(WhenStates.waiting_input)
async def process_when(message: Message, state: FSMContext):
    raw = (message.text or "").strip()
    if not raw:
        await message.answer("Пустой запрос. Пример: <code>Москва, завтра 18:30</code>", parse_mode="HTML")
        return

    place_part, time_part = _split_place_time(raw)

    # ── определяем локацию ─────────────────────────────────────────
    if place_part:
        coords = await geocode_city(place_part)
        if not coords:
            await message.answer(
                f"🔍 Не удалось найти место «{place_part}».\n"
                f"Попробуйте ещё раз или отмените: /cancel",
                parse_mode="HTML",
            )
            return
        lat, lon = coords
        city_name = place_part.strip().title()
    else:
        user = await get_user(message.from_user.id)
        if not user or not user.get("lat"):
            await message.answer(
                "📍 У вас не сохранён город. Укажите место явно:\n"
                "<code>Москва, завтра 18:30</code>",
                parse_mode="HTML",
            )
            return
        lat = user["lat"]
        lon = user["lon"]
        city_name = user.get("city") or ""

    # ── прогноз + локальная tz ─────────────────────────────────────
    fc = await get_forecast(lat, lon)
    if not fc or not fc.items:
        await message.answer("❌ Не удалось получить прогноз. Попробуйте позже.")
        return

    tz = timezone(timedelta(seconds=fc.timezone))
    now_utc = datetime.now(tz=timezone.utc)
    now_local_naive = now_utc.astimezone(tz).replace(tzinfo=None)

    dt_local = parse_user_time(time_part or raw, now_local_naive)
    if not dt_local:
        await message.answer(
            "🤔 Не понял время. Примеры:\n"
            "• <code>завтра 18:30</code>\n"
            "• <code>сегодня в 20</code>\n"
            "• <code>12.04 09:00</code>\n"
            "• <code>через 2 часа</code>",
            parse_mode="HTML",
        )
        return

    # локальное → UTC (через известный offset города)
    target_ts = int(dt_local.replace(tzinfo=tz).timestamp())
    now_ts = int(now_utc.timestamp())
    max_ts = fc.items[-1].dt

    if target_ts < now_ts - 3600:
        await message.answer("⏳ Указанное время в прошлом. Введите момент в будущем.")
        return
    if target_ts > max_ts + 3 * 3600:
        await message.answer(
            "📅 Прогноз доступен только на ближайшие <b>5 дней</b>.\n"
            "Выберите дату ближе к сегодняшнему дню.",
            parse_mode="HTML",
        )
        return

    item = interpolate_forecast(fc.items, target_ts)
    if not item:
        await message.answer("❌ Нет данных для указанного времени.")
        return

    await state.clear()

    text = _format_when_forecast(city_name or fc.city, dt_local, item)
    await message.answer(text, parse_mode="HTML", reply_markup=main_menu)


# ── helpers ─────────────────────────────────────────────────────────────

def _split_place_time(raw: str) -> tuple[str | None, str | None]:
    """Разделяет ввод на «место» и «время». Если разделителя нет — возвращает (None, raw)."""
    for sep in [",", ";", " — ", " – ", " - "]:
        if sep in raw:
            left, right = raw.split(sep, 1)
            left, right = left.strip(" ,;-—–"), right.strip(" ,;-—–")
            if left and right:
                return left, right
    return None, raw


def _format_when_forecast(city: str, dt_local: datetime, item: ForecastItem) -> str:
    wd = _WEEKDAYS_RU[dt_local.weekday()]
    when_str = f"{wd}, {dt_local.strftime('%d.%m')} в {dt_local.strftime('%H:%M')}"

    pressure_mmhg = round(item.pressure * 0.750062)
    wind_dir = wind_direction(item.wind_deg)
    pop = int(round(item.pop * 100))

    lines = [
        f"📍 <b>{city}</b>",
        f"🗓️ <b>{when_str}</b>",
        "",
        f"🌡️ <b>{item.temp:+.1f}°C</b> (ощущается {item.feels_like:+.1f}°C)",
        f"☁️ {item.description.capitalize() if item.description else '—'}",
        f"💧 Влажность: {item.humidity}%",
        f"🌬️ Ветер: {item.wind_speed:.1f} м/с ({wind_dir})",
        f"📊 Давление: {pressure_mmhg} мм рт. ст.",
        f"🌧️ Вероятность осадков: {pop}%",
    ]
    if item.rain_3h > 0:
        lines.append(f"☔ Ожидается дождь (~{item.rain_3h:.1f} мм за 3ч)")
    if item.snow_3h > 0:
        lines.append(f"❄️ Ожидается снег (~{item.snow_3h:.1f} мм за 3ч)")

    hint = _weather_hint(item)
    if hint:
        lines.append("")
        lines.append(f"💡 {hint}")

    return "\n".join(lines)


def _weather_hint(item: ForecastItem) -> str:
    if item.pop >= 0.6 or item.rain_3h >= 1:
        return "Скорее всего, будет дождь — возьмите зонт."
    if item.snow_3h >= 1:
        return "Ожидается снег — одевайтесь теплее."
    if item.temp <= 0:
        return "Будет морозно — тёплая одежда обязательна."
    if item.temp <= 10:
        return "Прохладно — возьмите куртку."
    if item.wind_speed >= 10:
        return "Сильный ветер — одевайтесь плотнее."
    if item.temp >= 25:
        return "Будет жарко — вода и головной убор кстати."
    return ""
