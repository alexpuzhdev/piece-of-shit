from aiogram.filters.callback_data import CallbackData


class MenuAction(CallbackData, prefix="menu"):
    """Callback data для главного меню."""
    action: str


# Действия главного меню
MENU_REPORTS = "reports"
MENU_BUDGET = "budget"
MENU_GOALS = "goals"
MENU_PLANNED = "planned"
MENU_SETTINGS = "settings"
MENU_BACK = "back"
MENU_DONATE = "donate"
MENU_FEEDBACK = "feedback"


class ReportAction(CallbackData, prefix="report"):
    """Callback data для подменю отчётов."""
    action: str


# Действия отчётов
REPORT_FULL = "full"
REPORT_EXPENSES = "expenses"
REPORT_INCOME = "income"
REPORT_CASHFLOW = "cashflow"
REPORT_BY_CATEGORY = "by_category"
REPORT_SELECT_PERIOD = "select_period"
REPORT_THIS_MONTH = "this_month"
REPORT_LAST_MONTH = "last_month"
REPORT_THIS_WEEK = "this_week"
REPORT_CONFIRM_DATES = "confirm_dates"
REPORT_CHANGE_DATES = "change_dates"


class BudgetAction(CallbackData, prefix="budget"):
    """Callback data для действий с бюджетом."""
    action: str


BUDGET_STATUS = "status"
BUDGET_SET = "set"
BUDGET_SET_CATEGORY = "set_cat"
BUDGET_CARRY_OVER = "carry_over"
BUDGET_CARRY_CONFIRM = "carry_confirm"
BUDGET_CARRY_DECLINE = "carry_decline"
BUDGET_RECOMMENDATION = "recommendation"


class GoalAction(CallbackData, prefix="goal"):
    """Callback data для целей накопления."""
    action: str
    goal_id: int = 0


GOAL_LIST = "list"
GOAL_CREATE = "create"
GOAL_ADD_AMOUNT = "add_amount"
GOAL_CLOSE = "close"
GOAL_ADD_ALL = "add_all"
GOAL_TOGGLE_FOR_ALL = "toggle_all"
GOAL_DISTRIBUTE_ALL = "distribute_all"
GOAL_DETAIL = "detail"


class PlannedAction(CallbackData, prefix="planned"):
    """Callback data для плановых трат."""
    action: str
    planned_id: int = 0


PLANNED_LIST = "list"
PLANNED_CREATE = "create"
PLANNED_COMPLETE = "complete"
PLANNED_RECORD = "record"


class SettingsAction(CallbackData, prefix="settings"):
    """Callback data для настроек."""
    action: str


SETTINGS_INCOME_SCHEDULE = "income_schedule"
SETTINGS_VACATION = "vacation"
SETTINGS_ADD_SCHEDULE = "add_schedule"
SETTINGS_ADD_VACATION = "add_vacation"
SETTINGS_FAMILY = "family"
SETTINGS_CREATE_FAMILY = "create_family"
SETTINGS_JOIN_FAMILY = "join_family"
SETTINGS_LEAVE_FAMILY = "leave_family"


class CategoryAction(CallbackData, prefix="cat"):
    """Callback data для управления категориями."""
    action: str
    category_id: int = 0


CAT_ADD_NEW = "add_new"
CAT_ADD_ALIAS = "add_alias"
CAT_USE_OTHER = "use_other"
CAT_SELECT = "select"


class FsmCancelAction(CallbackData, prefix="fsm_cancel"):
    """Callback для отмены текущего FSM-потока.
    return_to — callback, на который переходим после отмены."""
    return_to: str


class ConfirmAction(CallbackData, prefix="confirm"):
    """Универсальный callback для подтверждений (да/нет)."""
    action: str
    context: str = ""


# ═══════════════════════════════════════════════════════════
# Quick Entry (быстрый ввод: сумма → тип → категория)
# ═══════════════════════════════════════════════════════════

class QuickEntryAction(CallbackData, prefix="qe"):
    """Callback для быстрого ввода суммы без текста."""
    action: str
    category_id: int = 0


QE_TYPE_INCOME = "income"
QE_TYPE_EXPENSE = "expense"
QE_PICK_CATEGORY = "pick"
QE_CUSTOM_CATEGORY = "custom"


# ═══════════════════════════════════════════════════════════
# Управление категориями
# ═══════════════════════════════════════════════════════════

SETTINGS_CATEGORIES = "categories"

CAT_RENAME = "rename"
CAT_DELETE = "delete"
CAT_DELETE_CONFIRM = "del_confirm"


# ═══════════════════════════════════════════════════════════
# Подсказки
# ═══════════════════════════════════════════════════════════

class HintAction(CallbackData, prefix="hint"):
    """Callback для всплывающих подсказок в разделах."""
    section: str
