from aiogram import Dispatcher

from bot.core.handlers.budget import budget_router
from bot.core.handlers.cancel import cancel_router
from bot.core.handlers.categories import categories_router
from bot.core.handlers.expenses import expenses
from bot.core.handlers.goals import goals_router
from bot.core.handlers.hints import hints_router
from bot.core.handlers.feedback import feedback_router
from bot.core.handlers.menu import menu_router
from bot.core.handlers.planned import planned_router
from bot.core.handlers.quick_entry import quick_entry_router
from bot.core.handlers.recalculate import admin_router
from bot.core.handlers.reports import reports_router
from bot.core.handlers.settings import settings_router
from bot.core.handlers.start import start


def setup_handlers(dp: Dispatcher):
    """Регистрирует все роутеры.

    Порядок важен:
    1. cancel_router — перехватывает «Отмена» FSM раньше остальных.
    2. hints_router — обрабатывает «❓» подсказки.
    3. quick_entry_router — FSM быстрого ввода (callback + text в FSM-состоянии).
    4. categories_router — CRUD категорий (callback + FSM).
    5. Команды и callback-обработчики идут ДО catch-all expenses."""
    dp.include_routers(
        cancel_router,          # ❌ Отмена FSM (callback + /cancel)
        hints_router,           # ❓ Подсказки (callback)
        quick_entry_router,     # 💰 Быстрый ввод (callback + FSM)
        categories_router,      # 📁 Управление категориями (callback + FSM)
        start,                  # /start
        feedback_router,        # ✉️ Обратная связь (callback + FSM)
        menu_router,            # /menu + навигация по inline-кнопкам
        admin_router,           # /recalculate
        reports_router,         # Отчёты (callback + calendar FSM)
        budget_router,          # Бюджет (callback + FSM)
        goals_router,           # Цели (callback + FSM)
        planned_router,         # Плановые траты (callback + FSM)
        settings_router,        # Настройки (callback + FSM)
        expenses,               # Catch-all: расходы и доходы из текста
    )
