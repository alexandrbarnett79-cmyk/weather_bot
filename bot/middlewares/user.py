from __future__ import annotations
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update

from bot.database.db import upsert_user, get_user


class UserMiddleware(BaseMiddleware):
    """Регистрирует / обновляет пользователя при каждом обращении."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, Update) and event.message and event.message.from_user:
            tg_user = event.message.from_user
            await upsert_user(tg_user.id, tg_user.username)
            user = await get_user(tg_user.id)
        elif isinstance(event, Update) and event.callback_query and event.callback_query.from_user:
            tg_user = event.callback_query.from_user
            await upsert_user(tg_user.id, tg_user.username)
            user = await get_user(tg_user.id)

        data["db_user"] = user
        return await handler(event, data)
