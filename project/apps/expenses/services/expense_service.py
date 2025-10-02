from aiogram import types
from project.apps.core.models import User
from project.apps.expenses.models import Expense
from project.apps.expenses.services.category_service import CategoryService
from project.apps.expenses.services.expense_parser import ExpenseParser


class ExpenseService:
    @staticmethod
    async def create_from_message(user: User, message: types.Message) -> list[Expense]:
        items = ExpenseParser.parse(message.text or "")
        if not items:
            return []

        expenses = []
        for amount, category_name in items:
            category = await CategoryService.get_or_create(category_name)

            normalized_amount = abs(amount)

            expense = await Expense.objects.acreate(
                user=user,
                amount=normalized_amount,
                category=category,
                chat_id=message.chat.id,
                add_attr={
                    "message_id": message.message_id,
                    "date": message.date.isoformat() if message.date else None,
                    "raw_text": message.text,
                    "username": message.from_user.username if message.from_user else None,
                    "full_name": message.from_user.full_name if message.from_user else None,
                },
            )
            expenses.append(expense)

        return expenses
