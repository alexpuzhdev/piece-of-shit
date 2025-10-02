from aiogram import BaseMiddleware
from project.apps.core.services.user_start_service import UserService


class UserSyncMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        if hasattr(event, "from_user"):
            await UserService.get_or_create_from_aiogram(event.from_user)
        return await handler(event, data)
