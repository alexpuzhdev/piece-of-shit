from aiogram import types, Router, Bot
from aiogram.filters import CommandStart

from bot.core.keyboards.menu import main_menu_keyboard
from bot.core.texts import t
from bot.services.message_service import MessageService
from project.apps.core.services.user_start_service import UserService

start = Router()


@start.message(CommandStart())
async def start_command(message: types.Message, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)

    user, created = await UserService.get_or_create_from_aiogram(message.from_user)
    greeting = t("start.welcome") if created else t("start.welcome_back")
    await message.answer(greeting, reply_markup=main_menu_keyboard())
