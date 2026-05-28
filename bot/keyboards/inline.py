from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot.services.tone import TONES
from bot.services.recommendations import ACTIVITIES, HEALTH_MODES


def tone_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"tone:{key}")]
        for key, label in TONES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def activities_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"activity:{key}")]
        for key, label in ACTIVITIES.items()
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def health_keyboard() -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(text=label, callback_data=f"health_mode:{key}")]
        for key, label in HEALTH_MODES.items()
    ]
    buttons.append(
        [InlineKeyboardButton(text="🔄 Сброс профиля", callback_data="health_mode:reset")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def settings_keyboard(user: dict) -> InlineKeyboardMarkup:
    city_label = user.get("city") or "не задан"
    tone_label = TONES.get(user.get("tone", "neutral"), "⚪ Нейтральный")
    health_label = HEALTH_MODES.get(user.get("health_mode", ""), "не задан")

    buttons = [
        [InlineKeyboardButton(text=f"📍 Город: {city_label}", callback_data="settings:city")],
        [InlineKeyboardButton(text=f"🎭 Тон: {tone_label}", callback_data="settings:tone")],
        [InlineKeyboardButton(text=f"❤️ Здоровье: {health_label}", callback_data="settings:health")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def forecast_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⏱️ Почасовой (12ч)", callback_data="forecast:hourly"),
            InlineKeyboardButton(text="📆 На 5 дней", callback_data="forecast:5day"),
        ]
    ])
