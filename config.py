import tomllib
from collections import namedtuple
from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace
from typing import TypeVar, List, Generic

T = TypeVar('T')


class Config(Generic[T]):
    def __init__(self, path: Path | str):
        self._path = path
        self._load_config()

    @property
    def data(self) -> T:
        return self._data

    def _load_config(self):
        """
        Loads the configuration file, set data to the class representing its fields
        :return:
        """
        with open(self._path, 'rb') as file:
            toml_data = tomllib.load(file)

        self._data = SimpleNamespace()
        for section, keys in toml_data.items():
            section_tuple = namedtuple(section, [key for key in keys.keys()])
            setattr(self._data, section, section_tuple(*keys.values()))


@dataclass
class NotifierSection:
    api_id: int
    api_hash: str
    phone_number: str
    password: str

    key_words: List[str]
    unkey_words: List[str]
    chats: List[str]

    notify_chats: List[int]
    notify_message: str


@dataclass
class BotSection:
    author: str
    version: str
    description: str

    token: str
    throttling_delay: int


@dataclass
class BotConfig:
    Bot: BotSection
    Notifier: NotifierSection
