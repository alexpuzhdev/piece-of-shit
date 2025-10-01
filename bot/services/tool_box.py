from functools import cached_property

from bot.services.message_cleaner import MessageCleaner
from bot.services.message_updater import MessageUpdater


class Toolbox:
    def __init__(self, bot):
        self.bot = bot

    @cached_property
    def cleaner(self) -> MessageCleaner:
        return MessageCleaner(self.bot)

    @cached_property
    def updater(self):
        return MessageUpdater(self.bot)

