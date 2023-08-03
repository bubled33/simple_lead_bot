from aiogram import Router, F
from aiogram.types import Message

from config import Config, BotConfig
from keyboards import gen_about_markup

router = Router()


@router.message(F.text == '/about')
async def on_about(message: Message, config: Config[BotConfig]):
    markup = gen_about_markup(config)
    text = ('<b>Информация о боте</b>\n'
            f'<i>{config.data.Bot.description}</i>\n'
            f'<b>Версия: </b><code>{config.data.Bot.version}</code>\n'
            )
    await message.answer(text=text, reply_markup=markup)
