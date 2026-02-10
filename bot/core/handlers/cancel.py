"""Универсальный обработчик отмены FSM-потоков.

Ключевой принцип: при нажатии «Отмена» мы НЕ удаляем сообщение,
а редактируем его в родительское меню. Удаление приводит к ошибке
«message to edit not found», т.к. callback.message — это и есть
отслеживаемое сообщение.
"""

from aiogram import Router, types, Bot
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.core.callbacks.menu import (
    FsmCancelAction, MenuAction,
    MENU_BACK, MENU_BUDGET, MENU_GOALS, MENU_PLANNED, MENU_SETTINGS, MENU_REPORTS,
)
from bot.core.keyboards.menu import (
    main_menu_keyboard, budget_menu_keyboard, goals_menu_keyboard,
    planned_menu_keyboard, settings_menu_keyboard, reports_menu_keyboard,
)
from bot.core.texts import t
from bot.services.fsm_message_tracker import cleanup_tracked
from bot.services.message_service import MessageService

cancel_router = Router()

_MENU_MAP = {
    MENU_BUDGET: ("menu.budget.title", budget_menu_keyboard),
    MENU_GOALS: ("menu.goals.title", goals_menu_keyboard),
    MENU_PLANNED: ("menu.planned.title", planned_menu_keyboard),
    MENU_SETTINGS: ("menu.settings.title", settings_menu_keyboard),
    MENU_REPORTS: ("menu.reports.title", reports_menu_keyboard),
}


@cancel_router.callback_query(FsmCancelAction.filter())
async def fsm_cancel_callback(callback: types.CallbackQuery, callback_data: FsmCancelAction, state: FSMContext, bot: Bot):
    # Не вызываем cleanup_tracked() — она удалит сообщение, которое мы хотим отредактировать.
    # callback.message — это и есть tracked-сообщение (на нём кнопка «Отмена»).
    # Просто очищаем FSM-состояние и редактируем сообщение в меню.
    await state.clear()

    return_to = callback_data.return_to
    if return_to in _MENU_MAP:
        text_key, keyboard_fn = _MENU_MAP[return_to]
        try:
            await callback.message.edit_text(t(text_key), reply_markup=keyboard_fn())
        except Exception:
            await callback.message.answer(t(text_key), reply_markup=keyboard_fn())
    else:
        try:
            await callback.message.edit_text(t("menu.main.title"), reply_markup=main_menu_keyboard())
        except Exception:
            await callback.message.answer(t("menu.main.title"), reply_markup=main_menu_keyboard())

    await callback.answer(t("cancel.done"))


@cancel_router.message(Command("cancel"))
async def fsm_cancel_command(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)

    current_state = await state.get_state()
    if current_state is None:
        await message.answer(t("cancel.nothing"))
        return

    # Для /cancel — удаляем tracked-сообщение и отправляем новое меню
    await cleanup_tracked(bot, state)
    await state.clear()
    await message.answer(t("menu.main.title"), reply_markup=main_menu_keyboard())
