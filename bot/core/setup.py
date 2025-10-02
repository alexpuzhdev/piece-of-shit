from aiogram import Dispatcher

from bot.core.handlers.commands import commands
from bot.core.handlers.expenses import expenses
from bot.core.handlers.passive import listener
from bot.core.handlers.start import start


def setup_handlers(dp: Dispatcher):
    dp.include_routers(start, commands, listener, expenses)
