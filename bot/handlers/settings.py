from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database.db import get_user, update_user
from bot.keyboards.inline import settings_keyboard, tone_keyboard, health_keyboard
from bot.services.weather_api import geocode_city

router = Router()


class SettingsStates(StatesGroup):
    waiting_city = State()


@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала отправьте /start")
        return

    await message.answer(
        "⚙️ <b>Настройки</b>\n\nНажмите на пункт, чтобы изменить:",
        parse_mode="HTML",
        reply_markup=settings_keyboard(user),
    )


@router.callback_query(F.data == "settings:city")
async def ask_city(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("🏙️ Напишите название города:")
    await state.set_state(SettingsStates.waiting_city)
    await callback.answer()


@router.message(SettingsStates.waiting_city)
async def set_city(message: Message, state: FSMContext):
    city_name = message.text.strip()
    coords = await geocode_city(city_name)
    if not coords:
        await message.answer(f"Город «{city_name}» не найден. Попробуйте ещё раз:")
        return

    lat, lon = coords
    city = city_name.title()
    await update_user(message.from_user.id, lat=lat, lon=lon, city=city)
    await state.clear()

    user = await get_user(message.from_user.id)
    await message.answer(
        f"✅ Город изменён на <b>{city}</b>",
        parse_mode="HTML",
        reply_markup=settings_keyboard(user),
    )


@router.callback_query(F.data == "settings:tone")
async def ask_tone(callback: CallbackQuery):
    await callback.message.edit_text(
        "🎭 <b>Выберите тон подачи погоды:</b>",
        parse_mode="HTML",
        reply_markup=tone_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("tone:"))
async def set_tone(callback: CallbackQuery):
    tone = callback.data.split(":")[1]
    await update_user(callback.from_user.id, tone=tone)

    user = await get_user(callback.from_user.id)
    from bot.services.tone import TONES
    label = TONES.get(tone, tone)

    await callback.message.edit_text(
        f"✅ Тон изменён на <b>{label}</b>",
        parse_mode="HTML",
        reply_markup=settings_keyboard(user),
    )
    await callback.answer()


@router.callback_query(F.data == "settings:health")
async def ask_health(callback: CallbackQuery):
    await callback.message.edit_text(
        "❤️ <b>Выберите профиль здоровья:</b>",
        parse_mode="HTML",
        reply_markup=health_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("health_mode:"))
async def set_health_mode(callback: CallbackQuery):
    mode = callback.data.split(":")[1]
    if mode == "reset":
        await update_user(callback.from_user.id, health_mode="")
        msg = "🔄 Профиль здоровья сброшен"
    else:
        await update_user(callback.from_user.id, health_mode=mode)
        from bot.services.recommendations import HEALTH_MODES
        label = HEALTH_MODES.get(mode, mode)
        msg = f"✅ Профиль здоровья: <b>{label}</b>"

    user = await get_user(callback.from_user.id)
    await callback.message.edit_text(msg, parse_mode="HTML", reply_markup=settings_keyboard(user))
    await callback.answer()
