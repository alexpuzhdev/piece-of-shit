from aiogram import types

from project.apps.core.models import User
from project.apps.expenses.models import Income
from project.apps.expenses.services.category_service import CategoryService
from project.apps.expenses.services.income_parser import IncomeParser


class IncomeService:
    """Создание записей дохода из сообщений пользователя."""

    @staticmethod
    async def create_from_message(user: User, message: types.Message) -> list[Income]:
        items = IncomeParser.parse(message.text or "")
        if not items:
            return []

        incomes = []
        for amount, description in items:
            category = await CategoryService.get_or_create(description)

            income = await Income.objects.acreate(
                user=user,
                amount=abs(amount),
                category=category,
                description=description,
                chat_id=message.chat.id,
                add_attr={
                    "message_id": message.message_id,
                    "date": message.date.isoformat() if message.date else None,
                    "raw_text": message.text,
                    "username": message.from_user.username if message.from_user else None,
                    "full_name": message.from_user.full_name if message.from_user else None,
                },
            )
            incomes.append(income)

        return incomes

    @staticmethod
    async def create_quick(user: User, amount, category, chat_id: int) -> Income:
        """Создаёт доход из быстрого ввода (без парсинга сообщения)."""
        return await Income.objects.acreate(
            user=user,
            amount=abs(amount),
            category=category,
            description=category.name,
            chat_id=chat_id,
            add_attr={"source": "quick_entry"},
        )
