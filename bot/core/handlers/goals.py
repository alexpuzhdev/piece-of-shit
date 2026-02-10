from datetime import date
from decimal import Decimal, InvalidOperation

from aiogram import Router, types, Bot, F
from aiogram.fsm.context import FSMContext

from bot.core.callbacks.menu import (
    GoalAction, MenuAction,
    GOAL_LIST, GOAL_CREATE, GOAL_ADD_AMOUNT, GOAL_CLOSE, GOAL_ADD_ALL,
    GOAL_TOGGLE_FOR_ALL, GOAL_DISTRIBUTE_ALL, MENU_GOALS,
)
from bot.core.keyboards.menu import back_to_parent_keyboard, goals_menu_keyboard
from bot.core.states.goal_states import GoalStates
from bot.core.texts import t
from bot.services.fsm_message_tracker import (
    send_and_track, edit_and_track, cleanup_tracked, send_temporary, set_fsm_return_to,
)
from bot.services.message_service import MessageService
from bot.services.date_parser import parse_user_date
from project.apps.core.services.user_start_service import UserService
from project.apps.expenses.services.saving_goal_service import SavingGoalService

goals_router = Router()
_BACK_TO_GOALS = MenuAction(action=MENU_GOALS).pack()


async def _get_user(event):
    user, _ = await UserService.get_or_create_from_aiogram(event.from_user)
    return user


def _short_name(name: str, max_len: int = 14) -> str:
    if len(name) <= max_len:
        return name
    return name[: max_len - 1] + "…"


# ─── Список целей ──────────────────────────────────────

@goals_router.callback_query(GoalAction.filter(F.action == GOAL_LIST))
async def goal_list(callback: types.CallbackQuery, callback_data: GoalAction):
    user = await _get_user(callback)
    goals = await SavingGoalService.get_all_goals(user)

    if not goals:
        await callback.message.edit_text(t("goals.empty"), reply_markup=goals_menu_keyboard())
        await callback.answer()
        return

    lines = [t("goals.list.title")]
    for goal in goals:
        lines.append(SavingGoalService.format_goal(goal))
        if not goal.is_achieved:
            monthly_needed = await SavingGoalService.calculate_monthly_saving_needed(goal)
            if monthly_needed:
                lines.append(t("goals.monthly_hint", amount=f"{monthly_needed:.0f}"))
        lines.append("")

    inline_buttons = []
    for goal in goals:
        if not goal.is_achieved:
            short = _short_name(goal.name)
            inline_buttons.append([
                types.InlineKeyboardButton(
                    text=f"💰 {short}",
                    callback_data=GoalAction(action=GOAL_ADD_AMOUNT, goal_id=goal.id).pack(),
                ),
                types.InlineKeyboardButton(
                    text=f"✅ {short}",
                    callback_data=GoalAction(action=GOAL_CLOSE, goal_id=goal.id).pack(),
                ),
            ])
    inline_buttons.append([types.InlineKeyboardButton(text=t("btn.back"), callback_data=_BACK_TO_GOALS)])

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_buttons),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Завершить цель ────────────────────────────────────

@goals_router.callback_query(GoalAction.filter(F.action == GOAL_CLOSE))
async def goal_close(callback: types.CallbackQuery, callback_data: GoalAction):
    from asgiref.sync import sync_to_async
    from project.apps.expenses.models import SavingGoal

    @sync_to_async
    def get_goal():
        return SavingGoal.objects.filter(id=callback_data.goal_id).first()

    goal = await get_goal()
    if not goal:
        await callback.answer(t("goals.deposit.not_found"), show_alert=True)
        return
    if goal.is_achieved:
        await callback.answer(t("goals.already_achieved"), show_alert=True)
        return

    await SavingGoalService.close_goal(goal)
    await callback.answer(t("goals.close.success", name=goal.name))
    await goal_list(callback, GoalAction(action=GOAL_LIST))


# ─── Все накопления (сумма → выбор целей → распределить) ─

@goals_router.callback_query(GoalAction.filter(F.action == GOAL_ADD_ALL))
async def goal_add_all_start(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    user = await _get_user(callback)
    active = await SavingGoalService.get_active_goals(user)
    if not active:
        await callback.answer(t("goals.add_all.no_goals"), show_alert=True)
        return
    await state.set_state(GoalStates.entering_total_savings)
    await set_fsm_return_to(state, MENU_GOALS)
    await edit_and_track(callback.message, state, t("goals.add_all.prompt"))
    await callback.answer()


@goals_router.message(GoalStates.entering_total_savings)
async def goal_add_all_amount(message: types.Message, state: FSMContext, bot: Bot):
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

    active = await SavingGoalService.get_active_goals(await _get_user(message))
    if not active:
        await cleanup_tracked(bot, state)
        await state.clear()
        await send_temporary(bot, message.chat.id, t("goals.add_all.no_goals"))
        return

    await state.update_data(savings_total=str(amount), savings_goal_ids=[])
    await state.set_state(GoalStates.selecting_goals_savings)
    buttons = _build_goals_savings_keyboard(active, [])
    await send_and_track(
        bot, message.chat.id, state,
        t("goals.add_all.select_goals"),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
    )


def _build_goals_savings_keyboard(goals: list, selected_ids: list[int]) -> list:
    """Кнопки целей в 2 колонки (toggle) + кнопка Распределить."""
    rows = []
    row = []
    for goal in goals:
        prefix = "✓ " if goal.id in selected_ids else ""
        row.append(
            types.InlineKeyboardButton(
                text=f"{prefix}{_short_name(goal.name)}",
                callback_data=GoalAction(action=GOAL_TOGGLE_FOR_ALL, goal_id=goal.id).pack(),
            )
        )
        if len(row) == 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([
        types.InlineKeyboardButton(
            text=t("goals.add_all.distribute_btn"),
            callback_data=GoalAction(action=GOAL_DISTRIBUTE_ALL).pack(),
        ),
    ])
    return rows


@goals_router.callback_query(
    GoalStates.selecting_goals_savings,
    GoalAction.filter(F.action == GOAL_TOGGLE_FOR_ALL),
)
async def goal_toggle_for_savings(callback: types.CallbackQuery, callback_data: GoalAction, state: FSMContext, bot: Bot):
    data = await state.get_data()
    goal_ids = list(data.get("savings_goal_ids") or [])
    gid = callback_data.goal_id
    if gid in goal_ids:
        goal_ids.remove(gid)
    else:
        goal_ids.append(gid)
    await state.update_data(savings_goal_ids=goal_ids)

    user = await _get_user(callback)
    active = await SavingGoalService.get_active_goals(user)
    buttons = _build_goals_savings_keyboard(active, goal_ids)
    try:
        await callback.message.edit_reply_markup(reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons))
    except Exception:
        pass
    await callback.answer()


@goals_router.callback_query(
    GoalStates.selecting_goals_savings,
    GoalAction.filter(F.action == GOAL_DISTRIBUTE_ALL),
)
async def goal_distribute_savings(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    total_str = data.get("savings_total")
    goal_ids = data.get("savings_goal_ids") or []
    if not total_str or not goal_ids:
        await callback.answer(t("goals.add_all.select_at_least_one"), show_alert=True)
        return

    total = Decimal(total_str)
    updated = await SavingGoalService.distribute_to_goals(goal_ids, total)
    await cleanup_tracked(bot, state)
    await state.clear()
    await callback.message.edit_text(
        t("goals.add_all.success", amount=f"{total:.0f}", count=str(len(updated))),
        parse_mode="HTML",
    )
    await bot.send_message(callback.message.chat.id, t("menu.goals.title"), reply_markup=goals_menu_keyboard())
    await callback.answer()


# ─── Создание цели ─────────────────────────────────────

@goals_router.callback_query(GoalAction.filter(F.action == GOAL_CREATE))
async def goal_create_start(callback: types.CallbackQuery, callback_data: GoalAction, state: FSMContext, bot: Bot):
    await state.set_state(GoalStates.entering_name)
    await set_fsm_return_to(state, MENU_GOALS)
    await edit_and_track(callback.message, state, t("goals.create.name_prompt"))
    await callback.answer()


@goals_router.message(GoalStates.entering_name)
async def goal_enter_name(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)
    name = (message.text or "").strip()
    if not name:
        await send_and_track(bot, message.chat.id, state, t("error.empty_goal_name"))
        return
    await state.update_data(goal_name=name)
    await state.set_state(GoalStates.entering_target_amount)
    await send_and_track(bot, message.chat.id, state, t("goals.create.amount_prompt", name=name))


@goals_router.message(GoalStates.entering_target_amount)
async def goal_enter_amount(message: types.Message, state: FSMContext, bot: Bot):
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
    await state.update_data(target_amount=str(amount))
    await state.set_state(GoalStates.entering_deadline)
    await send_and_track(bot, message.chat.id, state, t("goals.create.deadline_prompt", amount=f"{amount:.0f}"))


@goals_router.message(GoalStates.entering_deadline)
async def goal_enter_deadline(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)
    text = (message.text or "").strip()
    deadline = None
    if text != "-":
        deadline = parse_user_date(text)
        if not deadline:
            await send_and_track(bot, message.chat.id, state, t("error.invalid_date_or_skip"))
            return

    data = await state.get_data()
    user = await _get_user(message)
    goal = await SavingGoalService.create_goal(
        user=user, name=data["goal_name"],
        target_amount=Decimal(data["target_amount"]), deadline=deadline,
    )
    await cleanup_tracked(bot, state)
    await state.clear()
    deadline_text = f"\n📅 Дедлайн: {deadline}" if deadline else ""
    await send_temporary(
        bot, message.chat.id,
        t("goals.create.success", name=goal.name, target_amount=f"{goal.target_amount:.0f}", deadline_text=deadline_text),
        delay_seconds=7,
    )
    await bot.send_message(message.chat.id, t("menu.goals.title"), reply_markup=goals_menu_keyboard())


# ─── Пополнение цели ──────────────────────────────────

@goals_router.callback_query(GoalAction.filter(F.action == GOAL_ADD_AMOUNT))
async def goal_add_amount_start(callback: types.CallbackQuery, callback_data: GoalAction, state: FSMContext, bot: Bot):
    await state.set_state(GoalStates.entering_deposit_amount)
    await set_fsm_return_to(state, MENU_GOALS)
    await state.update_data(goal_id=callback_data.goal_id)
    await edit_and_track(callback.message, state, t("goals.deposit.prompt"))
    await callback.answer()


@goals_router.message(GoalStates.entering_deposit_amount)
async def goal_deposit(message: types.Message, state: FSMContext, bot: Bot):
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
    goal_id = data.get("goal_id")

    from asgiref.sync import sync_to_async
    from project.apps.expenses.models import SavingGoal

    @sync_to_async
    def get_goal():
        return SavingGoal.objects.filter(id=goal_id).first()

    goal = await get_goal()
    if not goal:
        await cleanup_tracked(bot, state)
        await state.clear()
        await send_temporary(bot, message.chat.id, t("goals.deposit.not_found"))
        return

    goal = await SavingGoalService.add_to_goal(goal, amount)
    await cleanup_tracked(bot, state)
    await state.clear()
    achieved_text = t("goals.achieved") if goal.is_achieved else ""
    await send_temporary(
        bot, message.chat.id,
        t("goals.deposit.success", amount=f"{amount:.0f}", goal_info=SavingGoalService.format_goal(goal), achieved_text=achieved_text),
        delay_seconds=7,
    )
    await bot.send_message(message.chat.id, t("menu.goals.title"), reply_markup=goals_menu_keyboard())
