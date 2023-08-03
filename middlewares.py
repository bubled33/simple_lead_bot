from datetime import datetime
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from config import Config, BotConfig


class DataMiddleware(BaseMiddleware):
    def __init__(self, config: Config[BotConfig]):
        self._config = config

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        data['config'] = self._config
        await handler(event, data)


class ThrottlingMiddleware(BaseMiddleware):
    def __init__(self):
        self._last_updates: Dict[int, datetime] = dict()

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]], event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        throttling_delay = data['config'].data.Bot.throttling_delay
        now = datetime.now()
        if (last_update := self._last_updates.get(telegram_id := event.from_user.id)) and \
                (now - last_update).seconds < throttling_delay:
            return

        self._last_updates[telegram_id] = now
        await handler(event, data)
