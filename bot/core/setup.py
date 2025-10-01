from aiogram import Dispatcher

from bot.core.handlers.expenses import expenses
from bot.core.handlers.recalculate import admin_router
from bot.core.handlers.start import start


def setup_handlers(dp: Dispatcher):
    dp.include_routers(start, admin_router, expenses)
