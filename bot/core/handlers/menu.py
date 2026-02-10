from aiogram import Router, types, Bot
from aiogram.filters import Command

from bot.core.callbacks.menu import (
    MenuAction,
    MENU_REPORTS,
    MENU_BUDGET,
    MENU_GOALS,
    MENU_PLANNED,
    MENU_SETTINGS,
    MENU_BACK,
    MENU_DONATE,
    MENU_FEEDBACK,
)
from bot.core.keyboards.menu import (
    main_menu_keyboard,
    reports_menu_keyboard,
    budget_menu_keyboard,
    goals_menu_keyboard,
    planned_menu_keyboard,
    settings_menu_keyboard,
)
from bot.core.texts import t
from bot.services.message_service import MessageService

menu_router = Router()

MAIN_MENU_TEXT = t("menu.main.title")


@menu_router.message(Command("menu"))
async def menu_command(message: types.Message, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)
    await message.answer(t("menu.main.title"), reply_markup=main_menu_keyboard())


@menu_router.callback_query(MenuAction.filter())
async def menu_callback(
    callback: types.CallbackQuery,
    callback_data: MenuAction,
    bot: Bot,
):
    action = callback_data.action

    menu_map = {
        MENU_REPORTS: ("menu.reports.title", reports_menu_keyboard),
        MENU_BUDGET: ("menu.budget.title", budget_menu_keyboard),
        MENU_GOALS: ("menu.goals.title", goals_menu_keyboard),
        MENU_PLANNED: ("menu.planned.title", planned_menu_keyboard),
        MENU_SETTINGS: ("menu.settings.title", settings_menu_keyboard),
        MENU_BACK: ("menu.main.title", main_menu_keyboard),
    }

    if action == MENU_DONATE:
        await callback.answer(t("donate.in_progress"), show_alert=True)
        return

    if action == MENU_FEEDBACK:
        await callback.answer()
        return

    if action in menu_map:
        text_key, keyboard_fn = menu_map[action]
        await callback.message.edit_text(t(text_key), reply_markup=keyboard_fn())

    await callback.answer()
