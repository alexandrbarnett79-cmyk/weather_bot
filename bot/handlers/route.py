from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.services.weather_api import geocode_city, get_current_weather, WeatherData
from bot.services.recommendations import format_route_weather

router = Router()


class RouteStates(StatesGroup):
    waiting_route = State()


@router.message(F.text == "🗺️ Погода по пути")
async def ask_route(message: Message, state: FSMContext):
    await message.answer(
        "🗺️ <b>Погода по маршруту</b>\n\n"
        "Введите города через запятую.\n"
        "Пример: <code>Москва, Тула, Калуга</code>",
        parse_mode="HTML",
    )
    await state.set_state(RouteStates.waiting_route)


@router.message(RouteStates.waiting_route)
async def process_route(message: Message, state: FSMContext):
    raw = message.text.strip()
    separators = ["→", "->", ",", " - "]
    cities = [raw]
    for sep in separators:
        if sep in raw:
            cities = [c.strip() for c in raw.split(sep) if c.strip()]
            break

    if len(cities) < 2:
        await message.answer("Укажите как минимум 2 города. Пример: <code>Москва, Тула</code>", parse_mode="HTML")
        return

    await state.clear()
    await message.answer("⏳ Получаю погоду по маршруту…")

    results: list[tuple[str, WeatherData]] = []
    for city_name in cities:
        coords = await geocode_city(city_name)
        if not coords:
            await message.answer(f"⚠️ Город «{city_name}» не найден, пропускаю.")
            continue
        lat, lon = coords
        w = await get_current_weather(lat, lon)
        if w:
            w.city = city_name.title()
            results.append((city_name.title(), w))

    if not results:
        await message.answer("❌ Не удалось получить данные ни по одному городу.")
        return

    text = format_route_weather(results)
    await message.answer(text, parse_mode="HTML")
