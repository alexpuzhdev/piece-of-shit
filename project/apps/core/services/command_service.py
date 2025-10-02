from __future__ import annotations

from typing import Any, Awaitable, Callable, Mapping

from aiogram import Bot, types

from bot.services.message_service import MessageService
from project.apps.core.models import Command, CommandAlias
from project.apps.core.utils.text import normalize_command_text
from project.apps.expenses.services.report_service import ReportService

Handler = Callable[[Command, Mapping[str, Any]], Awaitable[None]]


class CommandService:
    _handlers: dict[str, Handler] = {}

    @staticmethod
    def normalize(text: str | None) -> str:
        return normalize_command_text(text)

    @classmethod
    async def match(cls, text: str | None) -> CommandAlias | None:
        normalized = cls.normalize(text)
        if not normalized:
            return None

        alias_qs = CommandAlias.objects.select_related("command").filter(
            normalized_alias=normalized
        )
        return await alias_qs.afirst()

    @classmethod
    async def execute(
        cls,
        command: Command,
        context: Mapping[str, Any],
    ) -> bool:
        if not command.is_active:
            return False

        handler = cls._handlers.get(command.code)
        if not handler:
            return False

        await handler(command, context)
        return True

    @classmethod
    def register(cls, code: str) -> Callable[[Handler], Handler]:
        def decorator(func: Handler) -> Handler:
            cls._handlers[code] = func
            return func

        return decorator


@CommandService.register("recalculate")
async def _execute_recalculate(command: Command, context: Mapping[str, Any]) -> None:
    message: types.Message | None = context.get("message")  # type: ignore[arg-type]
    bot: Bot | None = context.get("bot")  # type: ignore[arg-type]
    if not message or not bot:
        return

    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)

    chat_id = message.chat.id
    category_summary = await ReportService.get_category_summary(chat_id)

    if not category_summary:
        await message.answer("⚠️ В этом чате пока нет записанных расходов.")
        return

    total = await ReportService.get_total_by_chat(chat_id)

    lines = [
        f"{idx}. {category} — {amount:.2f} ₽"
        for idx, (category, amount) in enumerate(category_summary, start=1)
    ]
    text = "📊 Расходы по категориям:\n\n" + "\n".join(lines)
    text += f"\n\nВсего: {total:.2f} ₽"
    await message.answer(text)


@CommandService.register("stats")
async def _execute_stats(command: Command, context: Mapping[str, Any]) -> None:
    message: types.Message | None = context.get("message")  # type: ignore[arg-type]
    bot: Bot | None = context.get("bot")  # type: ignore[arg-type]
    if not message or not bot:
        return

    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)

    chat_id = message.chat.id
    expenses = await ReportService.get_expenses_by_chat(chat_id)
    total = await ReportService.get_total_by_chat(chat_id)

    if not expenses:
        await message.answer("⚠️ Статистика пока пуста — нет ни одного расхода.")
        return

    latest = expenses[-5:]
    latest_lines = [
        f"{idx}. {expense.category.name if expense.category else 'Без категории'} — {float(expense.amount):.2f} ₽ ({ReportService.format_date(expense)})"
        for idx, expense in enumerate(latest, start=1)
    ]

    text = "📈 Краткая статистика:\n\n"
    text += f"Всего расходов: {len(expenses)}\n"
    text += f"Сумма: {total:.2f} ₽\n\n"
    text += "Последние записи:\n" + "\n".join(latest_lines)
    await message.answer(text)


@CommandService.register("periods")
async def _execute_periods(command: Command, context: Mapping[str, Any]) -> None:
    message: types.Message | None = context.get("message")  # type: ignore[arg-type]
    bot: Bot | None = context.get("bot")  # type: ignore[arg-type]
    if not message or not bot:
        return

    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)

    text = (
        "📅 Доступные периоды бюджетов:\n"
        "• daily — Ежедневный\n"
        "• weekly — Еженедельный\n"
        "• monthly — Ежемесячный"
    )
    await message.answer(text)
