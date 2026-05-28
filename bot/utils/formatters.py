"""Утилиты для форматирования прогнозов."""

from __future__ import annotations
from datetime import datetime
from bot.services.weather_api import ForecastData, ForecastItem


def format_hourly(fc: ForecastData, hours: int = 12) -> str:
    """Почасовой прогноз (ближайшие N часов)."""
    items = fc.items[: hours // 3]
    if not items:
        return "Нет данных для почасового прогноза."

    lines = [f"⏱️ <b>Почасовой прогноз — {fc.city}</b>\n"]
    for item in items:
        time = item.dt_txt[11:16]
        pop = f" 💧{int(item.pop * 100)}%" if item.pop >= 0.2 else ""
        lines.append(
            f"  <b>{time}</b>  {item.temp:+.0f}°C  {item.description}{pop}"
        )
    return "\n".join(lines)


def format_5day(fc: ForecastData) -> str:
    """Прогноз на 5 дней (дневная / ночная температура)."""
    day_groups: dict[str, list[ForecastItem]] = {}
    for item in fc.items:
        day_key = item.dt_txt[:10]
        day_groups.setdefault(day_key, []).append(item)

    lines = [f"📆 <b>Прогноз на 5 дней — {fc.city}</b>\n"]
    for date_str, items in list(day_groups.items())[:5]:
        temps = [i.temp for i in items]
        min_t, max_t = min(temps), max(temps)
        max_pop = max(i.pop for i in items)
        desc = items[len(items) // 2].description

        dt = datetime.strptime(date_str, "%Y-%m-%d")
        day_name = _ru_weekday(dt.weekday())

        pop_str = f" 💧{int(max_pop * 100)}%" if max_pop >= 0.2 else ""
        lines.append(
            f"  <b>{day_name} {dt.strftime('%d.%m')}</b>: "
            f"{min_t:+.0f}…{max_t:+.0f}°C, {desc}{pop_str}"
        )
    return "\n".join(lines)


_WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]


def _ru_weekday(idx: int) -> str:
    return _WEEKDAYS_RU[idx]
