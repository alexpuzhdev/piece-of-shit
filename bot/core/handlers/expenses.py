
from aiogram import Router, types, Bot
from project.apps.core.services.user_start_service import UserService
from project.apps.expenses.services.expense_service import ExpenseService

expenses = Router()


@expenses.message()
async def save_expense(message: types.Message, bot: Bot):
    user, _ = await UserService.get_or_create_from_aiogram(message.from_user)
    expense = await ExpenseService.create_from_message(user, message)

    if expense:
        print(f"✅ Добавлен расход {expense.amount} ₽ на {expense.category}")
    else:
        print(f"⚠️ Не удалось распарсить сообщение: {message.text}")

