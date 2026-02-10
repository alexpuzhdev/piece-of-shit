from datetime import date
from decimal import Decimal, InvalidOperation

from aiogram import Router, types, Bot, F
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async

from bot.core.callbacks.menu import (
    BudgetAction,
    MenuAction,
    BUDGET_STATUS,
    BUDGET_SET,
    BUDGET_SET_CATEGORY,
    BUDGET_CARRY_OVER,
    BUDGET_CARRY_CONFIRM,
    BUDGET_CARRY_DECLINE,
    BUDGET_RECOMMENDATION,
    MENU_BUDGET,
)
from bot.core.keyboards.menu import back_to_parent_keyboard, budget_menu_keyboard
from bot.core.states.budget_states import BudgetStates
from bot.core.texts import t
from bot.services.fsm_message_tracker import (
    send_and_track, edit_and_track, cleanup_tracked, send_temporary, set_fsm_return_to,
)
from bot.services.message_service import MessageService
from project.apps.core.services.user_start_service import UserService
from project.apps.expenses.models import Budget, Category
from project.apps.expenses.services.budget_planning_service import BudgetPlanningService
from project.apps.expenses.services.category_service import CategoryService

budget_router = Router()

_BACK_TO_BUDGET = MenuAction(action=MENU_BUDGET).pack()


async def _get_user(event):
    user, _ = await UserService.get_or_create_from_aiogram(event.from_user)
    return user


# ─── Статус бюджета ────────────────────────────────────

@budget_router.callback_query(BudgetAction.filter(F.action == BUDGET_STATUS))
async def budget_status(callback: types.CallbackQuery, callback_data: BudgetAction):
    user = await _get_user(callback)
    today = date.today()

    general_status = await BudgetPlanningService.get_budget_status(user, today)

    @sync_to_async
    def get_category_budgets():
        return list(
            Budget.objects.filter(
                user=user, category__isnull=False, deleted_at__isnull=True,
            ).select_related("category").order_by("category__name")
        )

    category_budgets = await get_category_budgets()

    if not general_status and not category_budgets:
        await callback.message.edit_text(
            t("budget.not_configured"),
            reply_markup=budget_menu_keyboard(),
        )
        await callback.answer()
        return

    lines = [t("budget.status.title", month=f"{today:%B %Y}")]

    if general_status:
        icon = "🔴" if general_status.overspent else "🟢"
        lines.append(f"━━━ {icon} Общий ━━━")
        lines.append(f"Лимит: {general_status.limit:.0f} ₽")
        lines.append(f"Потрачено: {general_status.spent:.0f} ₽ ({general_status.usage_percent:.0f}%)")
        lines.append(f"Остаток: {general_status.remaining:.0f} ₽")
        if general_status.planned_upcoming > 0:
            lines.append(f"Плановые: {general_status.planned_upcoming:.0f} ₽")
        lines.append("")

    if category_budgets:
        lines.append("━━━ 📁 По категориям ━━━")
        for budget in category_budgets:
            cat_status = await BudgetPlanningService.get_budget_status(user, today, budget.category)
            if cat_status:
                icon = "🔴" if cat_status.overspent else "🟢"
                lines.append(
                    f"{icon} <b>{budget.category.name}</b>: "
                    f"{cat_status.spent:.0f} / {cat_status.limit:.0f} ₽ "
                    f"({cat_status.usage_percent:.0f}%)"
                )
            else:
                lines.append(f"📁 <b>{budget.category.name}</b>: {budget.limit:.0f} ₽")

    await callback.message.edit_text("\n".join(lines), reply_markup=back_to_parent_keyboard(_BACK_TO_BUDGET))
    await callback.answer()


# ─── Установка общего бюджета ──────────────────────────

@budget_router.callback_query(BudgetAction.filter(F.action == BUDGET_SET))
async def budget_set_start(callback: types.CallbackQuery, callback_data: BudgetAction, state: FSMContext, bot: Bot):
    await state.set_state(BudgetStates.entering_general_limit)
    await set_fsm_return_to(state, MENU_BUDGET)
    await edit_and_track(callback.message, state, t("budget.set.prompt"))
    await callback.answer()


@budget_router.message(BudgetStates.entering_general_limit)
async def budget_set_amount(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)

    text = (message.text or "").strip().replace(" ", "")
    try:
        amount = Decimal(text)
        if amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await send_and_track(bot, message.chat.id, state, t("error.invalid_amount"))
        return

    user = await _get_user(message)

    @sync_to_async
    def upsert_budget():
        return Budget.objects.update_or_create(
            user=user, category=None,
            defaults={"limit": amount, "period": "monthly"},
        )

    _, created = await upsert_budget()
    verb = "установлен" if created else "обновлён"

    await cleanup_tracked(bot, state)
    await state.clear()
    await send_temporary(bot, message.chat.id, t("budget.set.success", verb=verb, amount=f"{amount:.0f}"))
    await bot.send_message(message.chat.id, t("menu.budget.title"), reply_markup=budget_menu_keyboard())


# ─── Бюджет по категориям ─────────────────────────────

@budget_router.callback_query(BudgetAction.filter(F.action == BUDGET_SET_CATEGORY))
async def budget_set_category_start(callback: types.CallbackQuery, callback_data: BudgetAction, state: FSMContext, bot: Bot):
    categories = await CategoryService.get_all_categories()

    if not categories:
        await callback.message.edit_text(
            t("budget.category.no_categories"),
            reply_markup=back_to_parent_keyboard(_BACK_TO_BUDGET),
        )
        await callback.answer()
        return

    buttons = []
    for cat in categories:
        if cat.name == "Прочее":
            continue
        buttons.append([
            types.InlineKeyboardButton(text=f"📁 {cat.name}", callback_data=f"budget_cat_select:{cat.id}"),
        ])

    buttons.append([types.InlineKeyboardButton(text=t("btn.back"), callback_data=_BACK_TO_BUDGET)])
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.edit_text(t("budget.category.select_prompt"), reply_markup=keyboard)
    await callback.answer()


@budget_router.callback_query(F.data.startswith("budget_cat_select:"))
async def budget_category_selected(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    category_id = int(callback.data.split(":")[1])

    @sync_to_async
    def get_category():
        return Category.objects.filter(id=category_id).first()

    category = await get_category()
    if not category:
        await callback.answer(t("error.category_not_found"), show_alert=True)
        return

    await state.set_state(BudgetStates.entering_category_limit)
    await set_fsm_return_to(state, MENU_BUDGET)
    await state.update_data(budget_category_id=category_id, budget_category_name=category.name)
    await edit_and_track(callback.message, state, t("budget.category.amount_prompt", category=category.name))
    await callback.answer()


@budget_router.message(BudgetStates.entering_category_limit)
async def budget_category_amount(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)

    text = (message.text or "").strip().replace(" ", "")
    try:
        amount = Decimal(text)
        if amount <= 0:
            raise ValueError
    except (InvalidOperation, ValueError):
        await send_and_track(bot, message.chat.id, state, t("error.invalid_amount"))
        return

    data = await state.get_data()
    category_id = data["budget_category_id"]
    category_name = data["budget_category_name"]
    user = await _get_user(message)

    @sync_to_async
    def upsert():
        return Budget.objects.update_or_create(
            user=user, category_id=category_id,
            defaults={"limit": amount, "period": "monthly"},
        )

    _, created = await upsert()
    verb = "установлен" if created else "обновлён"

    await cleanup_tracked(bot, state)
    await state.clear()
    await send_temporary(bot, message.chat.id, t("budget.category.success", category=category_name, verb=verb, amount=f"{amount:.0f}"))
    await bot.send_message(message.chat.id, t("menu.budget.title"), reply_markup=budget_menu_keyboard())


# ─── Рекомендации ──────────────────────────────────────

@budget_router.callback_query(BudgetAction.filter(F.action == BUDGET_RECOMMENDATION))
async def budget_recommendation(callback: types.CallbackQuery, callback_data: BudgetAction):
    user = await _get_user(callback)
    recommendation = await BudgetPlanningService.get_budget_recommendation(user, date.today())
    text = t("budget.recommendation.title", text=recommendation) if recommendation else t("budget.recommendation.ok")
    await callback.message.edit_text(text, reply_markup=back_to_parent_keyboard(_BACK_TO_BUDGET))
    await callback.answer()


# ─── Перенос остатка ───────────────────────────────────

@budget_router.callback_query(BudgetAction.filter(F.action == BUDGET_CARRY_OVER))
async def budget_carry_over(callback: types.CallbackQuery, callback_data: BudgetAction):
    user = await _get_user(callback)
    today = date.today()
    prev_month = date(today.year - 1, 12, 1) if today.month == 1 else date(today.year, today.month - 1, 1)

    proposal = await BudgetPlanningService.calculate_carry_over(user, prev_month)
    if not proposal:
        await callback.message.edit_text(t("budget.carry.no_remainder"), reply_markup=back_to_parent_keyboard(_BACK_TO_BUDGET))
        await callback.answer()
        return

    carry_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text=t("btn.budget_carry_confirm"), callback_data=BudgetAction(action=BUDGET_CARRY_CONFIRM).pack()),
        types.InlineKeyboardButton(text=t("btn.budget_carry_decline"), callback_data=BudgetAction(action=BUDGET_CARRY_DECLINE).pack()),
    ]])

    await callback.message.edit_text(
        t("budget.carry.proposal",
          from_month=f"{proposal.from_month:%B %Y}",
          amount=f"{proposal.carry_over_amount:.0f}",
          to_month=f"{proposal.to_month:%B %Y}"),
        reply_markup=carry_keyboard,
    )
    await callback.answer()


@budget_router.callback_query(BudgetAction.filter(F.action == BUDGET_CARRY_CONFIRM))
async def budget_carry_confirm(callback: types.CallbackQuery, callback_data: BudgetAction):
    user = await _get_user(callback)
    today = date.today()
    prev_month = date(today.year - 1, 12, 1) if today.month == 1 else date(today.year, today.month - 1, 1)
    proposal = await BudgetPlanningService.calculate_carry_over(user, prev_month)

    if proposal:
        await BudgetPlanningService.apply_carry_over(user, proposal.to_month, proposal.carry_over_amount)
        await callback.message.edit_text(
            t("budget.carry.confirmed", amount=f"{proposal.carry_over_amount:.0f}", to_month=f"{proposal.to_month:%B %Y}"),
            reply_markup=back_to_parent_keyboard(_BACK_TO_BUDGET),
        )
    else:
        await callback.message.edit_text(t("budget.carry.error"), reply_markup=back_to_parent_keyboard(_BACK_TO_BUDGET))
    await callback.answer()


@budget_router.callback_query(BudgetAction.filter(F.action == BUDGET_CARRY_DECLINE))
async def budget_carry_decline(callback: types.CallbackQuery, callback_data: BudgetAction):
    await callback.message.edit_text(t("budget.carry.declined"), reply_markup=back_to_parent_keyboard(_BACK_TO_BUDGET))
    await callback.answer()
