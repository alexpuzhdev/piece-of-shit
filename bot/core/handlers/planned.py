from datetime import date
from decimal import Decimal, InvalidOperation

from aiogram import Router, types, Bot, F
from aiogram.fsm.context import FSMContext

from bot.core.callbacks.menu import (
    PlannedAction, MenuAction,
    PLANNED_LIST, PLANNED_CREATE, PLANNED_COMPLETE, PLANNED_RECORD, MENU_PLANNED,
)
from bot.core.keyboards.menu import back_to_parent_keyboard, planned_menu_keyboard
from bot.core.states.planned_states import PlannedStates
from bot.core.texts import t
from bot.services.fsm_message_tracker import (
    send_and_track, edit_and_track, cleanup_tracked, send_temporary, set_fsm_return_to,
)
from bot.services.message_service import MessageService
from bot.services.date_parser import parse_user_date
from project.apps.core.services.user_start_service import UserService
from project.apps.expenses.services.planned_expense_service import PlannedExpenseService

planned_router = Router()
_BACK_TO_PLANNED = MenuAction(action=MENU_PLANNED).pack()


async def _get_user(event):
    user, _ = await UserService.get_or_create_from_aiogram(event.from_user)
    return user


# ─── Список плановых трат ─────────────────────────────

@planned_router.callback_query(PlannedAction.filter(F.action == PLANNED_LIST))
async def planned_list(callback: types.CallbackQuery, callback_data: PlannedAction):
    user = await _get_user(callback)
    upcoming = await PlannedExpenseService.get_upcoming(user)
    overdue = await PlannedExpenseService.get_overdue(user)

    if not upcoming and not overdue:
        await callback.message.edit_text(t("planned.empty"), reply_markup=planned_menu_keyboard())
        await callback.answer()
        return

    lines = [t("planned.list.title")]
    if overdue:
        lines.append(t("planned.list.overdue"))
        for item in overdue:
            lines.append(PlannedExpenseService.format_planned(item))
        lines.append("")
    if upcoming:
        lines.append(t("planned.list.upcoming"))
        for item in upcoming:
            lines.append(PlannedExpenseService.format_planned(item))

    def _short(s: str, max_len: int = 14) -> str:
        return (s[: max_len - 1] + "…") if len(s) > max_len else s

    inline_buttons = []
    for item in overdue + upcoming:
        if not item.is_completed:
            short = _short(item.description)
            inline_buttons.append([
                types.InlineKeyboardButton(
                    text=f"✅ {short}",
                    callback_data=PlannedAction(action=PLANNED_COMPLETE, planned_id=item.id).pack(),
                ),
                types.InlineKeyboardButton(
                    text=f"💸 {short}",
                    callback_data=PlannedAction(action=PLANNED_RECORD, planned_id=item.id).pack(),
                ),
            ])
    inline_buttons.append([types.InlineKeyboardButton(text=t("btn.back"), callback_data=_BACK_TO_PLANNED)])

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_buttons),
        parse_mode="HTML",
    )
    await callback.answer()


# ─── Создание плановой траты ───────────────────────────

@planned_router.callback_query(PlannedAction.filter(F.action == PLANNED_CREATE))
async def planned_create_start(callback: types.CallbackQuery, callback_data: PlannedAction, state: FSMContext, bot: Bot):
    await state.set_state(PlannedStates.entering_description)
    await set_fsm_return_to(state, MENU_PLANNED)
    await edit_and_track(callback.message, state, t("planned.create.description_prompt"))
    await callback.answer()


@planned_router.message(PlannedStates.entering_description)
async def planned_enter_description(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)
    description = (message.text or "").strip()
    if not description:
        await send_and_track(bot, message.chat.id, state, t("error.empty_description"))
        return
    await state.update_data(description=description)
    await state.set_state(PlannedStates.entering_amount)
    await send_and_track(bot, message.chat.id, state, t("planned.create.amount_prompt", description=description))


@planned_router.message(PlannedStates.entering_amount)
async def planned_enter_amount(message: types.Message, state: FSMContext, bot: Bot):
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
    await state.update_data(amount=str(amount))
    await state.set_state(PlannedStates.entering_date)
    await send_and_track(bot, message.chat.id, state, t("planned.create.date_prompt", amount=f"{amount:.0f}"))


@planned_router.message(PlannedStates.entering_date)
async def planned_enter_date(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)
    text = (message.text or "").strip()
    planned_date = parse_user_date(text)
    if not planned_date:
        await send_and_track(bot, message.chat.id, state, t("error.invalid_date"))
        return
    await state.update_data(planned_date=planned_date.isoformat())
    await state.set_state(PlannedStates.entering_category)
    await send_and_track(bot, message.chat.id, state, t("planned.create.category_prompt", planned_date=str(planned_date)))


@planned_router.message(PlannedStates.entering_category)
async def planned_enter_category(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)
    text = (message.text or "").strip()
    category_name = text if text != "-" else None
    data = await state.get_data()
    user = await _get_user(message)

    planned = await PlannedExpenseService.create(
        user=user, amount=Decimal(data["amount"]),
        description=data["description"],
        planned_date=date.fromisoformat(data["planned_date"]),
        category_name=category_name,
    )
    await cleanup_tracked(bot, state)
    await state.clear()
    category_text = f"\n📁 Категория: {planned.category.name}" if planned.category else ""
    await send_temporary(
        bot, message.chat.id,
        t("planned.create.success",
          description=planned.description, amount=f"{planned.amount:.0f}",
          planned_date=str(planned.planned_date), category_text=category_text),
        delay_seconds=7,
    )
    await bot.send_message(message.chat.id, t("menu.planned.title"), reply_markup=planned_menu_keyboard())


# ─── Отметить как выполненную ──────────────────────────

@planned_router.callback_query(PlannedAction.filter(F.action == PLANNED_COMPLETE))
async def planned_complete(callback: types.CallbackQuery, callback_data: PlannedAction):
    from asgiref.sync import sync_to_async
    from project.apps.expenses.models import PlannedExpense

    @sync_to_async
    def get_planned():
        return PlannedExpense.objects.filter(id=callback_data.planned_id).first()

    planned = await get_planned()
    if not planned:
        await callback.answer(t("error.planned_not_found"), show_alert=True)
        return

    await PlannedExpenseService.complete(planned)
    await callback.answer(f"✅ «{planned.description}» отмечена как выполненная!")

    user = await _get_user(callback)
    upcoming = await PlannedExpenseService.get_upcoming(user)
    overdue = await PlannedExpenseService.get_overdue(user)

    if not upcoming and not overdue:
        await callback.message.edit_text(t("planned.all_done"), reply_markup=back_to_parent_keyboard(_BACK_TO_PLANNED))
        return

    lines = [t("planned.list.title") + " (обновлено)\n"]
    for item in overdue + upcoming:
        lines.append(PlannedExpenseService.format_planned(item))

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_to_parent_keyboard(_BACK_TO_PLANNED),
        parse_mode="HTML",
    )


# ─── Внести плановую трату ─────────────────────────────

@planned_router.callback_query(PlannedAction.filter(F.action == PLANNED_RECORD))
async def planned_record(callback: types.CallbackQuery, callback_data: PlannedAction, bot: Bot):
    from asgiref.sync import sync_to_async
    from project.apps.expenses.models import PlannedExpense
    from project.apps.expenses.services.expense_service import ExpenseService

    @sync_to_async
    def get_planned():
        return PlannedExpense.objects.filter(id=callback_data.planned_id).select_related("category").first()

    planned = await get_planned()
    if not planned:
        await callback.answer(t("error.planned_not_found"), show_alert=True)
        return

    if planned.is_completed:
        await callback.answer(t("planned.already_completed"), show_alert=True)
        return

    user = await _get_user(callback)
    expense = await ExpenseService.create_quick(
        user=user,
        amount=planned.amount,
        category=planned.category,
        chat_id=callback.message.chat.id,
    )
    await PlannedExpenseService.complete(planned, expense)
    await callback.answer(t("planned.recorded"))
    await planned_list(callback, PlannedAction(action=PLANNED_LIST))
