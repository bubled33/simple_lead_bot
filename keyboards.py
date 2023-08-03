from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import Config, BotConfig


def gen_about_markup(config: Config[BotConfig]):
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text='Разработчик', url=f't.me/{config.data.Bot.author}'))
    return builder.as_markup()
