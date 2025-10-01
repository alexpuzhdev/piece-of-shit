from aiogram import types
from .base_service import BaseService


class MessageUpdater(BaseService):
    async def update_bot_message(
            self,
            bot_message: types.Message,
            text: str,
            parse_mode: str | None = None,
            disable_web_page_preview: bool | None = None,
    ) -> None:
        try:
            await self.bot.edit_message_text(
                chat_id=bot_message.chat.id,
                message_id=bot_message.message_id,
                text=text,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview,
            )
        except Exception as e:
            self.logger(f"Не удалось обновить сообщение: {e}")
