from aiogram import Bot, Router, types

from bot.services.command_service import CommandService as BotCommandService
from project.apps.core.services.command_service import CommandService
from project.apps.core.services.user_start_service import UserService
from project.apps.expenses.services.expense_service import ExpenseService

expenses = Router()


@expenses.message()
async def save_expense(message: types.Message, bot: Bot):
    bot_command_service = BotCommandService(bot)
    handled = await bot_command_service.handle_message(message)
    if handled:
        return

    user, _ = await UserService.get_or_create_from_aiogram(message.from_user)

    alias = await CommandService.match(message.text)
    if alias:
        handled = await CommandService.execute(
            alias.command,
            {
                "message": message,
                "bot": bot,
                "user": user,
                "alias": alias,
            },
        )
        if handled:
            return

    expenses_list = await ExpenseService.create_from_message(user, message)

    if not expenses_list:
        await message.answer("⚠️ Не удалось распознать расход.")
    elif len(expenses_list) == 1:
        e = expenses_list[0]
        print(f"✅ Записал: {e.category.name} — {e.amount} ₽")
    else:
        print(
            "✅ Записал несколько расходов:\n"
            + "\n".join(
                f"{e.category.name} — {e.amount} ₽" for e in expenses_list
            )
        )
