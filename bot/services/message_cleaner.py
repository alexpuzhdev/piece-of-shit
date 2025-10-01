from aiogram import types

from .base_service import BaseService


class MessageCleaner(BaseService):
    async def delete_user_message(self, user_message: types.Message) -> None:
        try:
            await self.bot.delete_message(
                chat_id=user_message.chat.id,
                message_id=user_message.message_id,
            )
        except Exception:
            pass

    async def delete_bot_message(self, bot_message: types.Message) -> None:
        try:
            await self.bot.delete_message(
                chat_id=bot_message.chat.id,
                message_id=bot_message.message_id,
            )
        except Exception:
            pass

    async def clean(
            self,
            user_message: types.Message | None = None,
            bot_message: types.Message | None = None,
    ) -> None:

        if user_message:
            await self.delete_user_message(user_message)

        if bot_message:
            await self.delete_bot_message(bot_message)
