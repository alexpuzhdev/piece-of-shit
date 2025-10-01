from aiogram import Router, types, Bot
from aiogram.filters import Command

from bot.services.message_service import MessageService
from project.apps.expenses.services.report_service import ReportService

admin_router = Router()


@admin_router.message(Command("recalculate"))
async def recalculate_chat(message: types.Message, bot: Bot):
    chat_id = message.chat.id
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)
    expenses = await ReportService.get_expenses_by_chat(chat_id)

    if not expenses:
        await message.answer("⚠️ В этом чате пока нет записанных расходов.")
        return

    total = await ReportService.get_total_by_chat(chat_id)

    lines = [
        f"{e.category.name if e.category else 'Без категории'} - {e.amount:.2f} ₽ ({ReportService.format_date(e)})"
        for e in expenses[:20]
    ]

    text = "📊 Уже записанные расходы:\n\n"
    text += "\n".join(lines)
    text += f"\n\nВсего: {total:.2f} ₽"

    await message.answer(text)

