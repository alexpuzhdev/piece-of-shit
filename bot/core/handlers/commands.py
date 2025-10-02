from aiogram import Bot, Router, types
from aiogram.filters import Command

from project.apps.core.services.command_service import CommandService
from project.apps.core.services.user_start_service import UserService

commands = Router()


@commands.message(Command())
async def handle_command(message: types.Message, bot: Bot):
    user, _ = await UserService.get_or_create_from_aiogram(message.from_user)

    alias = await CommandService.match(message.text)
    if not alias:
        await message.answer("⚠️ Неизвестная команда.")
        return

    handled = await CommandService.execute(
        alias.command,
        {
            "message": message,
            "bot": bot,
            "user": user,
            "alias": alias,
        },
    )

    if not handled:
        await message.answer("⚠️ Команда временно недоступна.")
