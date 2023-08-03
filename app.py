import asyncio

from aiogram import Bot, Dispatcher
from loguru import logger

from config import Config, BotConfig
from handlers import router
from middlewares import DataMiddleware, ThrottlingMiddleware
from notifier import Notifier


async def main():
    config = Config[BotConfig]('settings.toml')
    bot, dispatcher = Bot(token=config.data.Bot.token, parse_mode='HTML'), Dispatcher()
    notifier = Notifier(phone_number=config.data.Notifier.phone_number,
                        password=config.data.Notifier.password,
                        api_id=config.data.Notifier.api_id,
                        api_hash=config.data.Notifier.api_hash,
                        bot=bot,
                        cache_path='files/cache.json')

    dispatcher.include_router(router)
    dispatcher.update.outer_middleware(DataMiddleware(config=config))
    dispatcher.message.outer_middleware(ThrottlingMiddleware())

    await asyncio.gather(dispatcher.start_polling(bot), notifier.start(key_words=config.data.Notifier.key_words,
                                                                       unkey_words=config.data.Notifier.key_words,
                                                                       chats=config.data.Notifier.chats,
                                                                       notify_chats=config.data.Notifier.notify_chats,
                                                                       notify_message=config.data.Notifier.notify_message,))

if __name__ == '__main__':
    try:
        logger.info('The bot was started!')
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info('The bot was stopped!')

