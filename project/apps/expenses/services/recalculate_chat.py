import asyncio
from django.core.management.base import BaseCommand
from aiogram import Bot
from django.conf import settings

from django.db.models import Q

from project.apps.core.services.user_start_service import UserService
from project.apps.expenses.services.expense_service import ExpenseService
from project.apps.expenses.models import Expense


class Command(BaseCommand):
    help = "Пересчитать чат: добавить расходы из сообщений, которые не были сохранены"

    def add_arguments(self, parser):
        parser.add_argument("chat_id", type=int, help="ID чата для пересчёта")
        parser.add_argument("--limit", type=int, default=1000, help="Сколько сообщений анализировать")

    def handle(self, *args, **options):
        chat_id = options["chat_id"]
        limit = options["limit"]
        asyncio.run(recalculate_chat(chat_id, limit))


async def recalculate_chat(chat_id: int, limit: int):
    bot = Bot(token=settings.BOT_TOKEN, parse_mode="HTML")

    print(f"🔄 Пересчитываем чат {chat_id} (limit={limit})...")

    async for message in bot.get_chat_history(chat_id=chat_id, limit=limit):
        if not message.text:
            continue

        exists = await Expense.objects.filter(
            Q(chat_id=chat_id) | Q(add_attr__chat_id=chat_id),
            add_attr__message_id=message.message_id,
        ).aexists()
        if exists:
            continue

        user, _ = await UserService.get_or_create_from_aiogram(message.from_user)

        expense = await ExpenseService.create_from_message(user, message)
        if expense:
            print(f"✅ Добавлен {expense.amount} ₽ на {expense.category} (msg {message.message_id})")
        else:
            print(f"⚠️ Пропущено сообщение {message.message_id}: {message.text[:30]}")
