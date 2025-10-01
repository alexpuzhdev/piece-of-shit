from aiogram import types
from aiogram.filters import CommandStart
from asgiref.sync import sync_to_async

from project.apps.core.services.user_start_service import UserService


class StartHandler:
    def __init__(self, dp):
        self.dp = dp
        self.register_handlers()

    def register_handlers(self):
        self.dp.message.register(self.start_command, CommandStart())

    async def start_command(self, message: types.Message):
        user, created = await UserService.get_or_create_from_aiogram(message.from_user)
        if created:
            await message.answer("✅ Добро пожаловать! Ты зарегистрирован.")
        else:
            await message.answer("👋 С возвращением!")
