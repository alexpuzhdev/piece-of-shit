"""Быстрый ввод: пользователь отправляет только сумму → выбирает тип → категорию.

Поток:
1. Пользователь отправляет число (например «1500»)
2. Бот показывает: [💰 Доход] [💸 Расход]
3. Пользователь выбирает тип → бот показывает список категорий
   - Для расхода — категории из расходов (в 2 столбика)
   - Для дохода — категории из доходов (если есть)
4. Пользователь нажимает кнопку ИЛИ пишет текстом → запись сохранена
"""

from decimal import Decimal, InvalidOperation

from aiogram import Router, types, Bot, F
from aiogram.fsm.context import FSMContext

from bot.core.callbacks.menu import (
    QuickEntryAction, QE_TYPE_INCOME, QE_TYPE_EXPENSE, QE_PICK_CATEGORY,
)
from bot.core.states.quick_entry_states import QuickEntryStates
from bot.core.texts import t
from bot.services.fsm_message_tracker import (
    send_and_track, cleanup_tracked, send_temporary,
)
from bot.services.group_notification_service import notify_group_about_expense, notify_group_about_income
from bot.services.message_service import MessageService
from bot.services.category_prompt_service import prompt_unknown_category
from bot.core.keyboards.menu import main_menu_keyboard
from project.apps.core.services.user_start_service import UserService
from project.apps.expenses.services.category_service import CategoryService
from project.apps.expenses.services.expense_service import ExpenseService
from project.apps.expenses.services.income_service import IncomeService

quick_entry_router = Router()


def _build_category_grid(categories, max_count: int = 12) -> list[list[types.InlineKeyboardButton]]:
    """Формирует сетку категорий в 2 столбика без эмодзи."""
    buttons = []
    row = []
    for cat in categories[:max_count]:
        row.append(
            types.InlineKeyboardButton(
                text=cat.name,
                callback_data=QuickEntryAction(action=QE_PICK_CATEGORY, category_id=cat.id).pack(),
            )
        )
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)
    return buttons


def _parse_amount_text(raw_text: str) -> Decimal | None:
    text = (raw_text or "").strip().replace(" ", "")
    if not text:
        return None
    if "," in text and "." not in text:
        text = text.replace(",", ".")
    try:
        amount = Decimal(text)
        return amount if amount > 0 else None
    except InvalidOperation:
        return None


async def _prompt_category_selection(
    bot: Bot,
    chat_id: int,
    state: FSMContext,
    entry_type: str,
    amount: str,
) -> None:
    if entry_type == QE_TYPE_INCOME:
        type_label = "доход"
        categories = await CategoryService.get_income_categories()
    else:
        type_label = "расход"
        categories = await CategoryService.get_expense_categories()

    buttons = _build_category_grid(categories)
    prompt = t("quick.choose_category", amount=amount, type_label=type_label)
    if not buttons:
        prompt += "\n\n" + t("quick.enter_category_text")

    await state.set_state(QuickEntryStates.choosing_category)
    await send_and_track(
        bot,
        chat_id,
        state,
        prompt,
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None,
    )


# ─── Выбор типа: доход / расход ───────────────────────

@quick_entry_router.callback_query(
    QuickEntryStates.choosing_type,
    QuickEntryAction.filter(F.action.in_({QE_TYPE_INCOME, QE_TYPE_EXPENSE})),
)
async def quick_entry_type_chosen(callback: types.CallbackQuery, callback_data: QuickEntryAction, state: FSMContext, bot: Bot):
    entry_type = callback_data.action
    await state.update_data(entry_type=entry_type)

    data = await state.get_data()
    amount = data["quick_amount"]

    await _prompt_category_selection(
        bot,
        callback.message.chat.id,
        state,
        entry_type=entry_type,
        amount=amount,
    )
    await callback.answer()


# ─── Выбор категории из кнопки ─────────────────────────

@quick_entry_router.callback_query(
    QuickEntryStates.choosing_category,
    QuickEntryAction.filter(F.action == QE_PICK_CATEGORY),
)
async def quick_entry_category_picked(callback: types.CallbackQuery, callback_data: QuickEntryAction, state: FSMContext, bot: Bot):
    from project.apps.expenses.models import Category
    category = await Category.objects.filter(id=callback_data.category_id).afirst()
    if not category:
        await callback.answer(t("error.category_not_found"), show_alert=True)
        return

    await _save_quick_entry(callback, state, bot, category)


# ─── Ввод категории текстом (на этапе choosing_category) ──

@quick_entry_router.message(QuickEntryStates.choosing_category)
async def quick_entry_text_category(message: types.Message, state: FSMContext, bot: Bot):
    """Пользователь вводит категорию текстом вместо нажатия кнопки."""
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)

    category_name = (message.text or "").strip()
    if not category_name:
        await send_and_track(bot, message.chat.id, state, t("error.empty_name"))
        return

    match_result = await CategoryService.match(category_name)
    category = match_result.category

    await _save_quick_entry_from_message(message, state, bot, category)
    if match_result.fell_back_to_other:
        await prompt_unknown_category(bot, message.chat.id, category_name)


# ─── Сохранение записи ─────────────────────────────────

async def _save_quick_entry(callback: types.CallbackQuery, state: FSMContext, bot: Bot, category):
    """Сохраняет запись из callback (нажатие на категорию)."""
    data = await state.get_data()
    amount = Decimal(data["quick_amount"])
    entry_type = data["entry_type"]
    chat_id = callback.message.chat.id

    user, _ = await UserService.get_or_create_from_aiogram(callback.from_user)

    # Не удаляем сообщение — редактируем в подтверждение
    await state.clear()

    if entry_type == QE_TYPE_INCOME:
        await IncomeService.create_quick(user, amount, category, chat_id)
        confirmation = t("income.confirmed_single", category=category.name, amount=f"{amount:.0f}")
        await notify_group_about_income(bot, user, category.name, f"{amount:.0f}")
    else:
        await ExpenseService.create_quick(user, amount, category, chat_id)
        confirmation = t("expense.confirmed_single", category=category.name, amount=f"{amount:.0f}")
        await notify_group_about_expense(bot, user, category.name, f"{amount:.0f}")

    try:
        await callback.message.edit_text(confirmation, parse_mode="HTML")
    except Exception:
        pass
    await send_temporary(bot, chat_id, confirmation, delay_seconds=5)
    await bot.send_message(chat_id, t("menu.main.title"), reply_markup=main_menu_keyboard())
    await callback.answer()


async def _save_quick_entry_from_message(message: types.Message, state: FSMContext, bot: Bot, category):
    """Сохраняет запись из текстового сообщения."""
    data = await state.get_data()
    amount = Decimal(data["quick_amount"])
    entry_type = data["entry_type"]
    chat_id = message.chat.id

    user, _ = await UserService.get_or_create_from_aiogram(message.from_user)

    await cleanup_tracked(bot, state)
    await state.clear()

    if entry_type == QE_TYPE_INCOME:
        await IncomeService.create_quick(user, amount, category, chat_id)
        confirmation = t("income.confirmed_single", category=category.name, amount=f"{amount:.0f}")
        await notify_group_about_income(bot, user, category.name, f"{amount:.0f}")
    else:
        await ExpenseService.create_quick(user, amount, category, chat_id)
        confirmation = t("expense.confirmed_single", category=category.name, amount=f"{amount:.0f}")
        await notify_group_about_expense(bot, user, category.name, f"{amount:.0f}")

    await send_temporary(bot, chat_id, confirmation, delay_seconds=5)
    await bot.send_message(chat_id, t("menu.main.title"), reply_markup=main_menu_keyboard())


@quick_entry_router.message(QuickEntryStates.entering_amount)
async def quick_entry_amount_entered(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)

    amount = _parse_amount_text(message.text or "")
    if amount is None:
        await send_and_track(bot, message.chat.id, state, t("error.invalid_amount"))
        return

    formatted_amount = f"{amount:.0f}"
    data = await state.get_data()
    entry_type = data.get("entry_type", QE_TYPE_EXPENSE)
    category_text = data.get("quick_category_text")

    await state.update_data(quick_amount=formatted_amount)

    if category_text and entry_type == QE_TYPE_EXPENSE:
        match_result = await CategoryService.match(category_text)
        category = match_result.category
        await _save_quick_entry_from_message(message, state, bot, category)
        if match_result.fell_back_to_other:
            await prompt_unknown_category(bot, message.chat.id, category_text)
        return

    await _prompt_category_selection(
        bot,
        message.chat.id,
        state,
        entry_type=entry_type,
        amount=formatted_amount,
    )
