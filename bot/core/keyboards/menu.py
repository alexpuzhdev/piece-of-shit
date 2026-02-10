from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.core.callbacks.menu import (
    MenuAction,
    ReportAction,
    BudgetAction,
    GoalAction,
    PlannedAction,
    SettingsAction,
    HintAction,
    MENU_REPORTS,
    MENU_BUDGET,
    MENU_GOALS,
    MENU_PLANNED,
    MENU_SETTINGS,
    MENU_BACK,
    MENU_DONATE,
    MENU_FEEDBACK,
    REPORT_FULL,
    REPORT_EXPENSES,
    REPORT_INCOME,
    REPORT_CASHFLOW,
    REPORT_THIS_MONTH,
    REPORT_LAST_MONTH,
    REPORT_THIS_WEEK,
    REPORT_SELECT_PERIOD,
    BUDGET_STATUS,
    BUDGET_SET,
    BUDGET_SET_CATEGORY,
    BUDGET_CARRY_OVER,
    BUDGET_RECOMMENDATION,
    GOAL_LIST,
    GOAL_CREATE,
    GOAL_ADD_ALL,
    PLANNED_LIST,
    PLANNED_CREATE,
    SETTINGS_INCOME_SCHEDULE,
    SETTINGS_VACATION,
    SETTINGS_ADD_SCHEDULE,
    SETTINGS_ADD_VACATION,
    SETTINGS_FAMILY,
    SETTINGS_CREATE_FAMILY,
    SETTINGS_JOIN_FAMILY,
    SETTINGS_CATEGORIES,
)
from bot.core.texts import t


def _back_button(callback_data: str, label: str | None = None) -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text=label or t("btn.back"), callback_data=callback_data)]


def _hint_row(section: str) -> list[InlineKeyboardButton]:
    """Кнопка «❓ Подсказка» на отдельной строке."""
    return [InlineKeyboardButton(text=t("btn.hint"), callback_data=HintAction(section=section).pack())]


def main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("btn.reports"), callback_data=MenuAction(action=MENU_REPORTS).pack()),
            InlineKeyboardButton(text=t("btn.budget"), callback_data=MenuAction(action=MENU_BUDGET).pack()),
        ],
        [
            InlineKeyboardButton(text=t("btn.goals"), callback_data=MenuAction(action=MENU_GOALS).pack()),
            InlineKeyboardButton(text=t("btn.planned"), callback_data=MenuAction(action=MENU_PLANNED).pack()),
        ],
        [InlineKeyboardButton(text=t("btn.settings"), callback_data=MenuAction(action=MENU_SETTINGS).pack())],
        [
            InlineKeyboardButton(text=t("btn.donate"), callback_data=MenuAction(action=MENU_DONATE).pack()),
            InlineKeyboardButton(text=t("btn.feedback"), callback_data=MenuAction(action=MENU_FEEDBACK).pack()),
        ],
        _hint_row("main_menu"),
    ])


def reports_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn.report_full"), callback_data=ReportAction(action=REPORT_FULL).pack())],
        [
            InlineKeyboardButton(text=t("btn.report_expenses"), callback_data=ReportAction(action=REPORT_EXPENSES).pack()),
            InlineKeyboardButton(text=t("btn.report_income"), callback_data=ReportAction(action=REPORT_INCOME).pack()),
        ],
        [InlineKeyboardButton(text=t("btn.report_cashflow"), callback_data=ReportAction(action=REPORT_CASHFLOW).pack())],
        [
            InlineKeyboardButton(text=t("btn.report_this_week"), callback_data=ReportAction(action=REPORT_THIS_WEEK).pack()),
            InlineKeyboardButton(text=t("btn.report_this_month"), callback_data=ReportAction(action=REPORT_THIS_MONTH).pack()),
        ],
        [
            InlineKeyboardButton(text=t("btn.report_last_month"), callback_data=ReportAction(action=REPORT_LAST_MONTH).pack()),
            InlineKeyboardButton(text=t("btn.report_select_period"), callback_data=ReportAction(action=REPORT_SELECT_PERIOD).pack()),
        ],
        _back_button(MenuAction(action=MENU_BACK).pack()),
        _hint_row("reports"),
    ])


def budget_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn.budget_status"), callback_data=BudgetAction(action=BUDGET_STATUS).pack())],
        [
            InlineKeyboardButton(text=t("btn.budget_set"), callback_data=BudgetAction(action=BUDGET_SET).pack()),
            InlineKeyboardButton(text=t("btn.budget_set_category"), callback_data=BudgetAction(action=BUDGET_SET_CATEGORY).pack()),
        ],
        [InlineKeyboardButton(text=t("btn.budget_recommendation"), callback_data=BudgetAction(action=BUDGET_RECOMMENDATION).pack())],
        [InlineKeyboardButton(text=t("btn.budget_carry_over"), callback_data=BudgetAction(action=BUDGET_CARRY_OVER).pack())],
        _back_button(MenuAction(action=MENU_BACK).pack()),
        _hint_row("budget"),
    ])


def goals_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn.goal_list"), callback_data=GoalAction(action=GOAL_LIST).pack())],
        [
            InlineKeyboardButton(text=t("btn.goal_create"), callback_data=GoalAction(action=GOAL_CREATE).pack()),
            InlineKeyboardButton(text=t("btn.goal_add_all"), callback_data=GoalAction(action=GOAL_ADD_ALL).pack()),
        ],
        _back_button(MenuAction(action=MENU_BACK).pack()),
        _hint_row("goals"),
    ])


def planned_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("btn.planned_list"), callback_data=PlannedAction(action=PLANNED_LIST).pack())],
        [InlineKeyboardButton(text=t("btn.planned_create"), callback_data=PlannedAction(action=PLANNED_CREATE).pack())],
        _back_button(MenuAction(action=MENU_BACK).pack()),
        _hint_row("planned"),
    ])


def settings_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t("btn.settings_schedules"), callback_data=SettingsAction(action=SETTINGS_INCOME_SCHEDULE).pack()),
            InlineKeyboardButton(text=t("btn.settings_add_schedule"), callback_data=SettingsAction(action=SETTINGS_ADD_SCHEDULE).pack()),
        ],
        [
            InlineKeyboardButton(text=t("btn.settings_vacations"), callback_data=SettingsAction(action=SETTINGS_VACATION).pack()),
            InlineKeyboardButton(text=t("btn.settings_add_vacation"), callback_data=SettingsAction(action=SETTINGS_ADD_VACATION).pack()),
        ],
        [InlineKeyboardButton(text=t("btn.settings_family"), callback_data=SettingsAction(action=SETTINGS_FAMILY).pack())],
        [
            InlineKeyboardButton(text=t("btn.settings_create_family"), callback_data=SettingsAction(action=SETTINGS_CREATE_FAMILY).pack()),
            InlineKeyboardButton(text=t("btn.settings_join_family"), callback_data=SettingsAction(action=SETTINGS_JOIN_FAMILY).pack()),
        ],
        [InlineKeyboardButton(text=t("btn.settings_categories"), callback_data=SettingsAction(action=SETTINGS_CATEGORIES).pack())],
        _back_button(MenuAction(action=MENU_BACK).pack()),
        _hint_row("settings"),
    ])


def back_to_parent_keyboard(parent_action_callback: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        _back_button(parent_action_callback),
    ])


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        _back_button(MenuAction(action=MENU_BACK).pack(), t("btn.back_to_menu")),
    ])
