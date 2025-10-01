from aiogram import types, Router, Bot
from aiogram.filters import CommandStart

from bot.services.tool_box import Toolbox
from project.apps.core.services.user_start_service import UserService

start = Router()


@start.message(CommandStart())
async def start_command(message: types.Message, bot: Bot):
    tool_box = Toolbox(bot)

    await tool_box.cleaner.delete_user_message(message)

    user, created = await UserService.get_or_create_from_aiogram(message.from_user)

    if created:
        await message.answer("✅ Добро пожаловать!")
    else:
        await message.answer("👋 С возвращением!")
