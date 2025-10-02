from aiogram import Router, types, Bot

from project.apps.core.services.user_start_service import UserService
from project.apps.expenses.services.expense_service import ExpenseService

expenses = Router()


@expenses.message()
async def save_expense(message: types.Message, bot: Bot):
    user, _ = await UserService.get_or_create_from_aiogram(message.from_user)
    expenses = await ExpenseService.create_from_message(user, message)

    if not expenses:
        await message.answer("⚠️ Не удалось распознать расход.")
    elif len(expenses) == 1:
        e = expenses[0]
        print(f"✅ Записал: {e.category.name} — {e.amount} ₽")
    else:
        print("✅ Записал несколько расходов:\n" + "\n".join(
            f"{e.category.name} — {e.amount} ₽" for e in expenses
        ))
