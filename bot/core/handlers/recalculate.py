from aiogram import Router, types, Bot
from aiogram.filters import Command

from bot.services import CommandService
from bot.services.message_service import MessageService
from project.apps.expenses.services.report_service import ReportService

admin_router = Router()


@admin_router.message(Command("recalculate"))
async def recalculate_chat(message: types.Message, bot: Bot):
    chat_id = message.chat.id
    tool_box = MessageService(bot)
    period = CommandService.parse_period(message.text or "")
    await tool_box.cleaner.delete_user_message(message)
    category_summary = await ReportService.get_category_summary(
        chat_id,
        start=period.start,
        end=period.end,
    )

    if not category_summary:
        await message.answer("⚠️ В этом чате пока нет записанных расходов.")
        return

    total = await ReportService.get_total_by_chat(
        chat_id,
        start=period.start,
        end=period.end,
    )

    lines = [
        f"{idx}. {category} — {amount:.2f} ₽"
        for idx, (category, amount) in enumerate(category_summary, start=1)
    ]
    suffix = f" {period.label}" if period.label else ""
    text = f"📊 Расходы по категориям{suffix}:\n\n"
    text += "\n".join(lines)
    text += f"\n\nВсего: {total:.2f} ₽"
    await message.answer(text)
