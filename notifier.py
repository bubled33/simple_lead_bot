import asyncio
import json
from contextlib import suppress
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, AsyncIterator
import re

from aiogram import Bot
from loguru import logger
from pyrogram import Client
from pyrogram.types import Message
from pyrogram.errors import FloodWait, ChatInvalid, UsernameInvalid


class Notifier:
    def __init__(self, api_id: int, api_hash: str, phone_number: str, password: str | None = None,
                 bot: Bot | None = None, cache_path: str | Path | None = None):
        self._client = Client(phone_number=phone_number,
                              password=password,
                              name=f'files/{phone_number}',
                              api_id=api_id,
                              api_hash=api_hash)
        self._bot = bot
        self._cache_path = cache_path

    async def init_client(self):
        """
        Initialize the telegram client. used when running the current file to create a session file
        :return:
        """
        await self._client.start()

    """
    Notifier
    """

    async def start(self, key_words: List[str], unkey_words: List[str], chats: List[str], notify_chats: List[int],
                    notify_message: str):
        """
        Launches the notifier, bypasses these chats on each lap,
         looking for new messages in them that meet the condition,
          and when found, sends them through chats. The delay between
          the start of the laps is constant - 30 minutes
        :param key_words: keys for validator
        :param unkey_words: unkeys for validator
        :param chats: chats for round parser
        :param notify_chats: chats for notify
        :param notify_message: pattern for notify
        :return:
        """

        self._init_cache(chats)
        await self._client.start()
        logger.debug('The notifier is running!')
        while True:
            last_notify_date = datetime.now()
            logger.debug('The notifier has started a round of checking chats')
            async for message in self._find_messages(key_words, unkey_words, chats):
                await self._notify(message, notify_chats, pattern=notify_message)
            logger.debug('The notifier has completed a round of checking chats')

            sleep_seconds = (timedelta(minutes=30) - (datetime.now() - last_notify_date)).seconds
            logger.debug(f'The notifier goes to sleep for {sleep_seconds} seconds')
            if sleep_seconds > 0:
                await asyncio.sleep(sleep_seconds)

    async def _notify(self, message: Message, notify_chats: List[int], pattern: str):
        """
        Notify the channel of a new message
        :param message: object for notify
        :param notify_chats: chats for notify
        :param pattern: a text pattern in which variables will be substituted at notification
        :return:
        """
        for chat in notify_chats:
            await self._bot.send_message(chat_id=chat, text=pattern.format(
                text=message.text,
                message_url=f'https://t.me/{message.chat.username}/{message.id}',
                author_url=f'https://t.me{username}' if (username := message.from_user.username) else 'Нет',
                date=message.date.strftime('%d.%m.%Y %H:%M')
            ))

    """
    Parser
    """

    async def _find_messages(self, key_words: List[str], unkey_words: List[str], chats: List[str]) -> AsyncIterator[
        Message
    ]:
        """
        Goes through chats and checks for new messages satisfying validation
        :param key_words: keys for search
        :param unkey_words: unkeys for search
        :param chats: chats for search
        :return: for each message found, the generator returns the message object
        """
        cache = self.get_cache()
        users = cache['users']
        with suppress(FloodWait, ChatInvalid, UsernameInvalid):
            for chat in chats:
                offset_date = datetime.fromtimestamp(cache['last_message'][chat])
                async for message in self._client.get_chat_history(chat_id=chat, offset=-1):
                    if offset_date > message.date:
                        break
                    if (user_id := message.from_user.id) in users:
                        continue
                    users.append(user_id)

                    if self._validate_text(message.text, key_words, unkey_words):
                        yield message

                cache['last_message'][chat] = datetime.now().timestamp()
                await asyncio.sleep(3.2)

        cache['users'] = users
        self.save_cache(cache)

    @classmethod
    def _validate_text(cls, text: str, key_words: List[str], unkey_words: List[str]) -> bool:
        """
        Checks text based on keys and exceptions
        :param text: string for check
        :param key_words: keys for check
        :param unkey_words: unkeys for check
        :return: True if validation is passed, if not, False
        """
        return bool(re.match(cls._build_regexp(key_words, unkey_words), text))

    @classmethod
    def _build_regexp(cls, key_words, unkey_words):
        """
        Build a regular expression to check for the presence of keywords and excluding words
        :param key_words: keys for regural expression
        :param unkey_words: unkeys for regural expression
        :return: regular expression
        """
        pattern = r'(?i)\b(?:{})\b'.format('|'.join(key_words))
        if unkey_words:
            pattern += r'(?!.*(?:{}))'.format('|'.join(unkey_words))
        logger.info(re.compile(pattern))
        return re.compile(pattern)

    """
    Cache
    """

    def save_cache(self, data: dict):
        """
        Save and update the notifier cache file
        :param data: data to save
        :return:
        """
        with open(self._cache_path, 'w') as file:
            return json.dump(data, file)

    def get_cache(self) -> dict:
        """
        Get the notifier cache file
        :return: The parsed toml file in the form of a dict
        """
        try:
            with open(self._cache_path, 'rb') as file:
                return json.load(file)
        except FileNotFoundError:
            with open(self._cache_path, 'w') as file:
                json.dump(base_cache := {'last_message': {}, 'users': []}, file)
            return base_cache

    def _init_cache(self, chats: List[str]):
        """
        Initializes the cache file based on configuration chats, setting the current date for empty sections
        :param chats:
        :return:
        """
        cache = self.get_cache()
        for chat in chats:
            if chat not in cache.get('last_message').keys():
                cache['last_message'][chat] = datetime.now().timestamp()
        self.save_cache(cache)


if __name__ == '__main__':
    from config import Config, BotConfig

    config = Config[BotConfig]('settings.toml')
    notifier = Notifier(phone_number=config.data.Notifier.phone_number,
                        password=config.data.Notifier.password,
                        api_id=config.data.Notifier.api_id,
                        api_hash=config.data.Notifier.api_hash)
    asyncio.run(notifier.init_client())
