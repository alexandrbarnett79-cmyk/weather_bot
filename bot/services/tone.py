"""Форматирование прогноза погоды в разных тональностях."""

from __future__ import annotations
from bot.services.weather_api import WeatherData, wind_direction

TONES = {
    "aggressive": "😤 Агрессивный",
    "soft": "😊 Мягкий",
    "happy": "😄 Счастливый",
    "sad": "😢 Грустный",
    "serious": "🧠 Серьёзный",
    "formal": "🏢 Формальный",
    "neutral": "⚪ Нейтральный",
}


def format_weather(w: WeatherData, tone: str = "neutral") -> str:
    """Главная функция — формирует сообщение о погоде в заданном тоне."""
    formatter = _FORMATTERS.get(tone, _neutral)
    return formatter(w)


def _header(w: WeatherData) -> str:
    return f"📍 <b>{w.city}</b>"


def _stats_block(w: WeatherData) -> str:
    pressure_mmhg = round(w.pressure * 0.750062)
    wd = wind_direction(w.wind_deg)
    return (
        f"🌡️ Температура: <b>{w.temp:+.1f}°C</b> (ощущается как {w.feels_like:+.1f}°C)\n"
        f"💧 Влажность: {w.humidity}%\n"
        f"🌬️ Ветер: {w.wind_speed:.1f} м/с ({wd})\n"
        f"📊 Давление: {pressure_mmhg} мм рт. ст.\n"
        f"☁️ Облачность: {w.clouds}%"
    )


# ── Тональные форматтеры ──────────────────────────────────────────────


def _aggressive(w: WeatherData) -> str:
    desc = w.description.capitalize()
    intro = f"{desc}. {w.temp:+.0f}°C"
    if w.rain_1h > 0:
        intro += ", дождь и сырость"
    if w.wind_speed >= 8:
        intro += f", ветер {w.wind_speed:.0f} м/с"
    intro += ". "

    body = "Без куртки и зонта выходить — отвратительная идея. " if w.temp < 15 else ""
    body += "Готовься заранее и не ной."

    return f"{_header(w)}\n\n😤 {intro}{body}\n\n{_stats_block(w)}"


def _soft(w: WeatherData) -> str:
    parts = [f"Сегодня около {w.temp:+.0f}°C."]
    if w.rain_1h > 0 or "дождь" in w.description.lower():
        parts.append("Возможен дождик, поэтому зонт будет кстати. ☔")
    if w.temp < 10:
        parts.append("Станет прохладнее — лучше взять курточку. 🧥")
    if w.wind_speed >= 8:
        parts.append(f"Ветерок ощутимый — {w.wind_speed:.0f} м/с.")

    return f"{_header(w)}\n\n😊 {' '.join(parts)}\n\n{_stats_block(w)}"


def _happy(w: WeatherData) -> str:
    parts = [f"Сегодня свежо и бодро — {w.temp:+.0f}°C! 🎉"]
    if w.rain_1h > 0 or "дождь" in w.description.lower():
        parts.append("Немного дождя добавит уюта 🌧️✨")
    if w.temp < 10:
        parts.append("Можно закутаться в куртку и наслаждаться прохладой!")
    if w.temp >= 20:
        parts.append("Прекрасный день для приключений! ☀️")

    return f"{_header(w)}\n\n😄 {' '.join(parts)}\n\n{_stats_block(w)}"


def _sad(w: WeatherData) -> str:
    parts = [f"Сегодня всего {w.temp:+.0f}°C."]
    if w.rain_1h > 0 or "дождь" in w.description.lower():
        parts.append("Будет дождь…")
    if w.temp < 10:
        parts.append("К вечеру станет ещё холоднее.")
    parts.append("Не самый приятный день для прогулок… 😔")

    return f"{_header(w)}\n\n😢 {' '.join(parts)}\n\n{_stats_block(w)}"


def _serious(w: WeatherData) -> str:
    pressure_mmhg = round(w.pressure * 0.750062)
    wd = wind_direction(w.wind_deg)
    parts = [
        f"Температура воздуха — около {w.temp:+.0f}°C.",
        f"Атмосферное давление: {pressure_mmhg} мм рт. ст.",
    ]
    if w.rain_1h > 0 or "дождь" in w.description.lower():
        parts.append("Ожидаются осадки.")
    if w.wind_speed >= 5:
        parts.append(f"Ветер {w.wind_speed:.0f} м/с, направление — {wd}.")
    parts.append("Рекомендуется учитывать условия при планировании.")

    return f"{_header(w)}\n\n🧠 {' '.join(parts)}\n\n{_stats_block(w)}"


def _formal(w: WeatherData) -> str:
    parts = [
        f"В течение дня ожидается температура около {w.temp:+.0f}°C.",
        f"Состояние: {w.description}.",
    ]
    if w.rain_1h > 0:
        parts.append("Возможны осадки в виде дождя.")
    if w.wind_speed >= 5:
        parts.append(f"Ветер до {w.wind_speed:.0f} м/с.")
    parts.append("Рекомендуется учитывать погодные условия при планировании передвижений.")

    return f"{_header(w)}\n\n🏢 {' '.join(parts)}\n\n{_stats_block(w)}"


def _neutral(w: WeatherData) -> str:
    parts = [
        f"Сегодня {w.temp:+.0f}°C. {w.description.capitalize()}.",
    ]
    if w.rain_1h > 0:
        parts.append("Дождь.")
    if w.wind_speed >= 5:
        parts.append(f"Ветер {w.wind_speed:.0f} м/с.")

    return f"{_header(w)}\n\n⚪ {' '.join(parts)}\n\n{_stats_block(w)}"


_FORMATTERS = {
    "aggressive": _aggressive,
    "soft": _soft,
    "happy": _happy,
    "sad": _sad,
    "serious": _serious,
    "formal": _formal,
    "neutral": _neutral,
}
