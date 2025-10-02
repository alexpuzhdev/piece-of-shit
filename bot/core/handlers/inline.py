from aiogram import Bot, Router, types

from bot.services.command_service import CommandService


inline = Router()


@inline.inline_query()
async def inline_query_handler(query: types.InlineQuery, bot: Bot):
    service = CommandService(bot)
    results = await service.handle_inline_query(query)

    await query.answer(results, is_personal=True, cache_time=0)


@inline.chosen_inline_result()
async def chosen_inline_result_handler(result: types.ChosenInlineResult, bot: Bot):
    service = CommandService(bot)
    await service.on_chosen_inline_result(result)
