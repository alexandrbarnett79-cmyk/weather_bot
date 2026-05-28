import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BOT_TOKEN, TELEGRAM_PROXY
from bot.database.db import init_db
from bot.handlers import start, weather, settings, activities, route, health, when

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    if not BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN не задан. Создайте .env файл (см. .env.example)")

    await init_db()

    session = AiohttpSession(proxy=TELEGRAM_PROXY) if TELEGRAM_PROXY else None
    if TELEGRAM_PROXY:
        logger.info("Используется прокси для Telegram API")

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML"),
        session=session,
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_routers(
        start.router,
        settings.router,
        activities.router,
        route.router,
        health.router,
        when.router,
        weather.router,  # последним — содержит fallback-хендлер для текста
    )

    logger.info("Бот запущен!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
