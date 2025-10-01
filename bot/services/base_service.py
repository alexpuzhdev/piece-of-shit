import logging
from functools import cached_property

from aiogram import Bot


class BaseService:
    def __init__(self, bot: Bot):
        self.bot = bot

    @cached_property
    def logger(self):
        return logging.getLogger(__name__)
