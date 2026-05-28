"""Рекомендации по одежде, активностям и самочувствию."""

from __future__ import annotations
from bot.services.weather_api import WeatherData, ForecastItem


# ---------------------------------------------------------------------------
# Одежда / что взять с собой
# ---------------------------------------------------------------------------

def clothing_advice(w: WeatherData) -> list[str]:
    tips: list[str] = []
    t = w.temp

    if t <= -20:
        tips.append("Пуховик, тёплая шапка, шарф, перчатки и тёплая обувь — обязательно")
    elif t <= -10:
        tips.append("Зимняя куртка, шапка, перчатки и тёплая обувь")
    elif t <= 0:
        tips.append("Тёплая куртка или пальто, шапка и перчатки")
    elif t <= 10:
        tips.append("Демисезонная куртка и лёгкая шапка")
    elif t <= 18:
        tips.append("Лёгкая куртка или толстовка")
    elif t <= 25:
        tips.append("Футболка и лёгкие штаны")
    else:
        tips.append("Лёгкая одежда, шорты, головной убор от солнца")

    if w.rain_1h > 0 or "дождь" in w.description.lower():
        tips.append("Возьмите зонт — ожидается дождь ☔")

    if w.snow_1h > 0 or "снег" in w.description.lower():
        tips.append("Возможен снег — оденьтесь теплее ❄️")

    if w.wind_speed >= 10:
        tips.append("Сильный ветер — ветрозащитная одежда будет кстати 💨")

    if t <= -5 and w.wind_speed >= 5:
        tips.append("Гололёд вероятен — выбирайте обувь с нескользкой подошвой")

    if t >= 25 and w.clouds < 30:
        tips.append("Солнцезащитные очки и крем от загара 🕶️")

    return tips


def rain_soon_warning(forecast_items: list[ForecastItem]) -> str | None:
    """Предупреждение если дождь начнётся в ближайшие часы."""
    for item in forecast_items[:3]:
        if item.pop >= 0.5 or item.rain_3h > 0:
            return f"Ожидается дождь около {item.dt_txt[11:16]} (вероятность {int(item.pop * 100)}%)"
    return None


# ---------------------------------------------------------------------------
# Активности
# ---------------------------------------------------------------------------

ACTIVITIES = {
    "walk": "🚶 Прогулка",
    "commute": "🏢 Работа / учёба",
    "sport": "🏃 Спорт на улице",
    "drive": "🚗 Поездка / дорога",
    "hangout": "☕ Отдых и встречи",
}


def activity_advice(activity: str, w: WeatherData) -> str:
    t = w.temp
    wind = w.wind_speed
    rain = w.rain_1h > 0 or "дождь" in w.description.lower()

    if activity == "walk":
        if rain:
            return "Для прогулки сейчас не лучшее время — дождь. Лучше подождать ☔"
        if t < -15:
            return "Слишком холодно для прогулки. Если выходите — одевайтесь максимально тепло 🥶"
        if wind >= 15:
            return "Сильный ветер — прогулка будет некомфортной 💨"
        if 15 <= t <= 25 and not rain and wind < 8:
            return "Идеальная погода для прогулки! Наслаждайтесь 🌤️"
        return "Прогулка возможна, но оденьтесь по погоде"

    if activity == "commute":
        parts = []
        if rain:
            parts.append("возьмите зонт ☔")
        if t <= 0:
            parts.append("возможен гололёд — будьте осторожны")
        if wind >= 12:
            parts.append("сильный ветер — учитывайте при движении")
        if not parts:
            return "Дорога должна быть комфортной 👍"
        return "В дорогу: " + ", ".join(parts)

    if activity == "sport":
        if rain:
            return "Для спорта на улице не лучшее время — дождь ☔"
        if t < -10:
            return "Слишком холодно для спорта на улице 🥶"
        if t > 33:
            return "Слишком жарко — высок риск перегрева. Лучше перенести тренировку 🥵"
        if wind >= 15:
            return "Сильный ветер — бег или велосипед будут тяжелее 💨"
        if 10 <= t <= 22:
            return "Отличные условия для спорта на улице! 💪"
        return "Спорт на улице возможен, но следите за самочувствием"

    if activity == "drive":
        parts = []
        if rain:
            parts.append("мокрая дорога — снижайте скорость")
        if w.snow_1h > 0:
            parts.append("снег — будьте особенно осторожны")
        if w.visibility < 2000:
            parts.append("низкая видимость — включите фары")
        if t <= -3 and (w.humidity > 80 or w.rain_1h > 0):
            parts.append("гололёд вероятен")
        if not parts:
            return "Дорожные условия хорошие 🚗"
        return "На дороге: " + ", ".join(parts)

    if activity == "hangout":
        if rain:
            return "Лучше встретиться в помещении — на улице дождь ☔"
        if 15 <= t <= 28 and wind < 8:
            return "Прекрасная погода для встречи на открытом воздухе! ☀️"
        return "Можно встретиться, но комфортнее будет в помещении"

    return "Нет данных по этой активности"


# ---------------------------------------------------------------------------
# Здоровье и самочувствие
# ---------------------------------------------------------------------------

HEALTH_MODES = {
    "meteo": "🌡️ Метеочувствительный",
    "hyper": "💓 Гипертоник",
    "allergy": "🤧 Аллергик",
}


def health_advice(mode: str, w: WeatherData) -> list[str]:
    tips: list[str] = []
    pressure_hpa = w.pressure
    pressure_mmhg = round(pressure_hpa * 0.750062)

    if mode == "meteo":
        if pressure_mmhg < 740:
            tips.append(f"Давление пониженное ({pressure_mmhg} мм рт. ст.) — возможны головные боли")
        elif pressure_mmhg > 770:
            tips.append(f"Давление повышенное ({pressure_mmhg} мм рт. ст.) — берегите себя")
        if w.humidity > 85:
            tips.append("Высокая влажность — может ощущаться духота")
        if abs(w.temp - w.feels_like) > 5:
            tips.append("Большая разница между реальной и ощущаемой температурой — оденьтесь с запасом")

    elif mode == "hyper":
        if pressure_mmhg < 740:
            tips.append(f"Давление низкое ({pressure_mmhg} мм рт. ст.) — следите за самочувствием")
        elif pressure_mmhg > 760:
            tips.append(f"Давление повышенное ({pressure_mmhg} мм рт. ст.) — избегайте перенапряжения")
        if w.temp > 30:
            tips.append("Жара — пейте больше воды, избегайте солнца")

    elif mode == "allergy":
        if w.wind_speed > 5 and w.humidity < 50 and 5 < w.temp < 30:
            tips.append("Сухой ветер — возможна повышенная концентрация пыльцы 🌿")
        if w.humidity > 80:
            tips.append("Высокая влажность — может быть легче для аллергиков")
        if "дождь" in w.description.lower():
            tips.append("После дождя воздух чище — хорошее время для выхода")

    if not tips:
        tips.append("По вашему профилю особых предупреждений нет 👍")

    return tips


# ---------------------------------------------------------------------------
# Маршрут
# ---------------------------------------------------------------------------

def format_route_weather(cities_weather: list[tuple[str, WeatherData]]) -> str:
    lines = ["🗺️ <b>Погода по маршруту:</b>\n"]
    for city, w in cities_weather:
        emoji = _weather_emoji(w)
        lines.append(
            f"📍 <b>{city}</b>: {emoji} {w.temp:+.0f}°C, "
            f"{w.description}, ветер {w.wind_speed:.0f} м/с"
        )
    return "\n".join(lines)


def _weather_emoji(w: WeatherData) -> str:
    desc = w.description.lower()
    if "дождь" in desc or "ливень" in desc:
        return "🌧️"
    if "снег" in desc:
        return "🌨️"
    if "облач" in desc or "пасмурн" in desc:
        return "☁️"
    if "ясно" in desc or "безоблачн" in desc:
        return "☀️"
    if "туман" in desc:
        return "🌫️"
    if "гроз" in desc:
        return "⛈️"
    return "🌤️"
