from datetime import date, timedelta

from aiogram import Router, types, Bot, F
from aiogram.fsm.context import FSMContext

from bot.core.callbacks.calendar import CalendarAction, CAL_PREV_MONTH, CAL_NEXT_MONTH, CAL_SELECT_DAY, CAL_IGNORE
from bot.core.callbacks.menu import (
    ReportAction, MenuAction,
    REPORT_FULL, REPORT_EXPENSES, REPORT_INCOME, REPORT_CASHFLOW,
    REPORT_THIS_MONTH, REPORT_LAST_MONTH, REPORT_THIS_WEEK,
    REPORT_SELECT_PERIOD, REPORT_CONFIRM_DATES, REPORT_CHANGE_DATES,
    MENU_REPORTS,
)
from bot.core.keyboards.calendar import build_calendar_keyboard
from bot.core.keyboards.menu import back_to_parent_keyboard, reports_menu_keyboard
from bot.core.states.report_states import ReportStates
from bot.core.texts import t
from project.apps.core.services.user_start_service import UserService
from project.apps.expenses.services.report_service import ReportService

reports_router = Router()
_BACK_TO_REPORTS = MenuAction(action=MENU_REPORTS).pack()


def _this_month_range() -> tuple[date, date]:
    today = date.today()
    return today.replace(day=1), today


def _last_month_range() -> tuple[date, date]:
    today = date.today()
    first_day_this = today.replace(day=1)
    last_day_prev = first_day_this - timedelta(days=1)
    return last_day_prev.replace(day=1), last_day_prev


def _this_week_range() -> tuple[date, date]:
    today = date.today()
    return today - timedelta(days=today.weekday()), today


async def _get_user_id(callback: types.CallbackQuery) -> int:
    user, _ = await UserService.get_or_create_from_aiogram(callback.from_user)
    return user.id


async def _generate_report(user_id: int, report_type: str, date_from: date, date_to: date) -> str:
    if report_type == REPORT_EXPENSES:
        summary = await ReportService.get_expense_category_summary_by_period(user_id, date_from, date_to)
        total = await ReportService.get_expense_total_by_period(user_id, date_from, date_to)
        return ReportService.format_expense_report(summary, total, date_from, date_to)
    elif report_type == REPORT_INCOME:
        summary = await ReportService.get_income_category_summary_by_period(user_id, date_from, date_to)
        total = await ReportService.get_income_total_by_period(user_id, date_from, date_to)
        return ReportService.format_income_report(summary, total, date_from, date_to)
    elif report_type == REPORT_CASHFLOW:
        income_total = await ReportService.get_income_total_by_period(user_id, date_from, date_to)
        expense_total = await ReportService.get_expense_total_by_period(user_id, date_from, date_to)
        return ReportService.format_cashflow_report(income_total, expense_total, date_from, date_to)
    else:
        expense_summary = await ReportService.get_expense_category_summary_by_period(user_id, date_from, date_to)
        expense_total = await ReportService.get_expense_total_by_period(user_id, date_from, date_to)
        income_summary = await ReportService.get_income_category_summary_by_period(user_id, date_from, date_to)
        income_total = await ReportService.get_income_total_by_period(user_id, date_from, date_to)
        return ReportService.format_full_report(
            expense_summary, expense_total, income_summary, income_total, date_from, date_to,
        )


# ─── Quick-period reports ──────────────────────────────

@reports_router.callback_query(ReportAction.filter(F.action == REPORT_THIS_MONTH))
async def report_this_month(callback: types.CallbackQuery, callback_data: ReportAction):
    user_id = await _get_user_id(callback)
    date_from, date_to = _this_month_range()
    text = await _generate_report(user_id, REPORT_FULL, date_from, date_to)
    await callback.message.edit_text(text, reply_markup=back_to_parent_keyboard(_BACK_TO_REPORTS))
    await callback.answer()


@reports_router.callback_query(ReportAction.filter(F.action == REPORT_LAST_MONTH))
async def report_last_month(callback: types.CallbackQuery, callback_data: ReportAction):
    user_id = await _get_user_id(callback)
    date_from, date_to = _last_month_range()
    text = await _generate_report(user_id, REPORT_FULL, date_from, date_to)
    await callback.message.edit_text(text, reply_markup=back_to_parent_keyboard(_BACK_TO_REPORTS))
    await callback.answer()


@reports_router.callback_query(ReportAction.filter(F.action == REPORT_THIS_WEEK))
async def report_this_week(callback: types.CallbackQuery, callback_data: ReportAction):
    user_id = await _get_user_id(callback)
    date_from, date_to = _this_week_range()
    text = await _generate_report(user_id, REPORT_FULL, date_from, date_to)
    await callback.message.edit_text(text, reply_markup=back_to_parent_keyboard(_BACK_TO_REPORTS))
    await callback.answer()


# ─── Typed reports ─────────────────────────────────────

@reports_router.callback_query(
    ReportAction.filter(F.action.in_({REPORT_FULL, REPORT_EXPENSES, REPORT_INCOME, REPORT_CASHFLOW}))
)
async def report_typed(callback: types.CallbackQuery, callback_data: ReportAction):
    user_id = await _get_user_id(callback)
    date_from, date_to = _this_month_range()
    text = await _generate_report(user_id, callback_data.action, date_from, date_to)
    await callback.message.edit_text(text, reply_markup=back_to_parent_keyboard(_BACK_TO_REPORTS))
    await callback.answer()


# ─── Calendar-based period selection ───────────────────

@reports_router.callback_query(ReportAction.filter(F.action == REPORT_SELECT_PERIOD))
async def report_select_period_start(callback: types.CallbackQuery, callback_data: ReportAction, state: FSMContext):
    await state.set_state(ReportStates.choosing_start_date)
    await state.update_data(report_type=REPORT_FULL)
    await callback.message.edit_text(t("reports.select_start_date"), reply_markup=build_calendar_keyboard())
    await callback.answer()


@reports_router.callback_query(ReportStates.choosing_start_date, CalendarAction.filter(F.action == CAL_SELECT_DAY))
async def calendar_start_date_selected(callback: types.CallbackQuery, callback_data: CalendarAction, state: FSMContext):
    selected_date = date(callback_data.year, callback_data.month, callback_data.day)
    await state.update_data(date_from=selected_date.isoformat())
    await state.set_state(ReportStates.choosing_end_date)
    await callback.message.edit_text(
        t("reports.start_selected", date_from=str(selected_date)),
        reply_markup=build_calendar_keyboard(year=callback_data.year, month=callback_data.month),
    )
    await callback.answer()


@reports_router.callback_query(ReportStates.choosing_end_date, CalendarAction.filter(F.action == CAL_SELECT_DAY))
async def calendar_end_date_selected(callback: types.CallbackQuery, callback_data: CalendarAction, state: FSMContext):
    data = await state.get_data()
    date_from = date.fromisoformat(data["date_from"])
    date_to = date(callback_data.year, callback_data.month, callback_data.day)
    await state.update_data(date_to=date_to.isoformat())

    confirm_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text=t("btn.report_confirm"), callback_data=ReportAction(action=REPORT_CONFIRM_DATES).pack()),
        types.InlineKeyboardButton(text=t("btn.report_change"), callback_data=ReportAction(action=REPORT_CHANGE_DATES).pack()),
    ]])
    await callback.message.edit_text(
        t("reports.confirm_period", date_from=str(date_from), date_to=str(date_to)),
        reply_markup=confirm_keyboard,
    )
    await callback.answer()


@reports_router.callback_query(ReportAction.filter(F.action == REPORT_CONFIRM_DATES))
async def report_confirm_dates(callback: types.CallbackQuery, callback_data: ReportAction, state: FSMContext):
    data = await state.get_data()
    date_from = date.fromisoformat(data["date_from"])
    date_to = date.fromisoformat(data["date_to"])
    report_type = data.get("report_type", REPORT_FULL)
    await state.clear()
    user_id = await _get_user_id(callback)
    text = await _generate_report(user_id, report_type, date_from, date_to)
    await callback.message.edit_text(text, reply_markup=back_to_parent_keyboard(_BACK_TO_REPORTS))
    await callback.answer()


@reports_router.callback_query(ReportAction.filter(F.action == REPORT_CHANGE_DATES))
async def report_change_dates(callback: types.CallbackQuery, callback_data: ReportAction, state: FSMContext):
    await state.set_state(ReportStates.choosing_start_date)
    await callback.message.edit_text(t("reports.select_start_date"), reply_markup=build_calendar_keyboard())
    await callback.answer()


# ─── Calendar navigation ──────────────────────────────

@reports_router.callback_query(CalendarAction.filter(F.action.in_({CAL_PREV_MONTH, CAL_NEXT_MONTH})))
async def calendar_navigate(callback: types.CallbackQuery, callback_data: CalendarAction):
    await callback.message.edit_reply_markup(
        reply_markup=build_calendar_keyboard(year=callback_data.year, month=callback_data.month),
    )
    await callback.answer()


@reports_router.callback_query(CalendarAction.filter(F.action == CAL_IGNORE))
async def calendar_ignore(callback: types.CallbackQuery):
    await callback.answer()
