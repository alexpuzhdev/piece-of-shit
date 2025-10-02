import logging

from aiogram import Router, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent

from project.apps.core.services.command_service import CommandService

listener = Router()

logger = logging.getLogger(__name__)


@listener.inline_query()
async def handle_inline_query(inline_query: types.InlineQuery):
    alias = await CommandService.match(inline_query.query)

    results: list[InlineQueryResultArticle] = []
    if alias:
        command = alias.command
        results.append(
            InlineQueryResultArticle(
                id=f"command-{command.id}-{alias.id}",
                title=command.name or alias.alias,
                description=command.description or alias.alias,
                input_message_content=InputTextMessageContent(
                    message_text=alias.alias
                ),
            )
        )

    await inline_query.answer(results, cache_time=1, is_personal=True)
