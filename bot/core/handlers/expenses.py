"""Обработка текстовых сообщений: расходы, доходы, быстрый ввод."""

import asyncio
import re
from decimal import Decimal, InvalidOperation

from aiogram import Router, types, Bot, F
from aiogram.fsm.context import FSMContext

from bot.core.callbacks.menu import (
    CategoryAction, QuickEntryAction,
    CAT_ADD_NEW, CAT_ADD_ALIAS, CAT_SELECT, CAT_USE_OTHER,
    QE_TYPE_INCOME, QE_TYPE_EXPENSE,
)
from bot.core.states.quick_entry_states import QuickEntryStates
from bot.core.texts import t
from bot.services.fsm_message_tracker import send_temporary, set_fsm_return_to, send_and_track
from bot.services.group_notification_service import notify_group_about_expense, notify_group_about_income
from bot.services.message_service import MessageService
from bot.services.category_prompt_service import prompt_unknown_category
from project.apps.core.services.user_start_service import UserService
from project.apps.expenses.services.category_service import CategoryService
from project.apps.expenses.services.expense_parser import ExpenseParser
from project.apps.expenses.services.expense_service import ExpenseService
from project.apps.expenses.services.income_parser import IncomeParser
from project.apps.expenses.services.income_service import IncomeService

expenses = Router()

CONFIRMATION_DELETE_DELAY = 5

# Регулярка для определения «голого числа» без текста категории
_PURE_AMOUNT_RE = re.compile(
    r"^\s*(\d[\d\s.,]*)\s*(?:₽|руб\.?|rub)?\s*$",
    re.IGNORECASE,
)

_TYPE_ONLY_WORDS = {
    "доход": QE_TYPE_INCOME,
    "расход": QE_TYPE_EXPENSE,
}


def _parse_pure_amount(text: str) -> Decimal | None:
    """Пытается распознать сообщение как одиночное число без категории."""
    match = _PURE_AMOUNT_RE.match(text.strip())
    if not match:
        return None
    raw = match.group(1).replace("\xa0", "").replace(" ", "")
    # Нормализация десятичного разделителя
    if "." in raw and "," in raw:
        last_dot = raw.rfind(".")
        last_comma = raw.rfind(",")
        if last_dot > last_comma:
            raw = raw.replace(",", "")
        else:
            raw = raw.replace(".", "").replace(",", ".")
    elif "," in raw:
        tail = raw.split(",")[-1]
        if 1 <= len(tail) <= 2:
            raw = raw.replace(",", ".")
        else:
            raw = raw.replace(",", "")
    elif "." in raw:
        tail = raw.split(".")[-1]
        if len(tail) > 2:
            raw = raw.replace(".", "")
    try:
        amount = Decimal(raw)
        return amount if amount > 0 else None
    except InvalidOperation:
        return None


def _is_category_only(text: str) -> bool:
    stripped = (text or "").strip()
    if not stripped or stripped.startswith("/"):
        return False
    if re.search(r"\d", stripped):
        return False
    return bool(re.search(r"[A-Za-zА-Яа-яЁё]", stripped))


async def _start_quick_amount_flow(
    bot: Bot,
    state: FSMContext,
    chat_id: int,
    entry_type: str,
    category_text: str | None = None,
) -> None:
    await state.set_state(QuickEntryStates.entering_amount)
    await set_fsm_return_to(state, "back")
    await state.update_data(entry_type=entry_type, quick_category_text=category_text)

    type_label = "доход" if entry_type == QE_TYPE_INCOME else "расход"
    prompt = t("quick.enter_amount", type_label=type_label)
    if category_text:
        prompt = t("quick.enter_amount_with_category", type_label=type_label, category=category_text)
    await send_and_track(bot, chat_id, state, prompt)


@expenses.message()
async def save_expense_or_income(message: types.Message, bot: Bot, state: FSMContext):
    tool_box = MessageService(bot)
    user, _ = await UserService.get_or_create_from_aiogram(message.from_user)
    text = message.text or ""

    # ─── Быстрый ввод: голое число → доход/расход → категория ──
    pure_amount = _parse_pure_amount(text)
    if pure_amount is not None:
        await tool_box.cleaner.delete_user_message(message)

        await state.set_state(QuickEntryStates.choosing_type)
        await set_fsm_return_to(state, "back")

        formatted_amount = f"{pure_amount:.0f}"
        await state.update_data(quick_amount=formatted_amount, quick_chat_id=message.chat.id)

        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [
                types.InlineKeyboardButton(
                    text=t("btn.quick_income"),
                    callback_data=QuickEntryAction(action=QE_TYPE_INCOME).pack(),
                ),
                types.InlineKeyboardButton(
                    text=t("btn.quick_expense"),
                    callback_data=QuickEntryAction(action=QE_TYPE_EXPENSE).pack(),
                ),
            ],
        ])

        msg = await bot.send_message(
            chat_id=message.chat.id,
            text=t("quick.choose_type", amount=formatted_amount),
            reply_markup=keyboard,
        )
        await state.update_data(
            _tracked_bot_msg_id=msg.message_id,
            _tracked_chat_id=message.chat.id,
        )
        return

    # ─── Быстрый ввод: тип без суммы ─────────────────────
    normalized = (text or "").strip().lower()
    if normalized in _TYPE_ONLY_WORDS:
        await tool_box.cleaner.delete_user_message(message)
        await _start_quick_amount_flow(
            bot,
            state,
            message.chat.id,
            entry_type=_TYPE_ONLY_WORDS[normalized],
        )
        return

    # ─── Быстрый ввод: категория без суммы ───────────────
    if _is_category_only(text):
        await tool_box.cleaner.delete_user_message(message)
        await _start_quick_amount_flow(
            bot,
            state,
            message.chat.id,
            entry_type=QE_TYPE_EXPENSE,
            category_text=text.strip(),
        )
        return

    # ─── Доход ─────────────────────────────────────────
    if IncomeParser.is_income_message(text):
        incomes = await IncomeService.create_from_message(user, message)
        await tool_box.cleaner.delete_user_message(message)

        if not incomes:
            await send_temporary(bot, message.chat.id, t("income.parse_error"))
            return

        if len(incomes) == 1:
            income = incomes[0]
            category_name = income.category.name if income.category else "без категории"
            confirmation = t("income.confirmed_single", category=category_name, amount=f"{income.amount:.0f}")
        else:
            lines = [t("income.confirmed_multi", count=str(len(incomes)))]
            for income in incomes:
                category_name = income.category.name if income.category else "без категории"
                lines.append(f"  • {category_name} — +{income.amount:.0f} ₽")
            confirmation = "\n".join(lines)

        await send_temporary(bot, message.chat.id, confirmation, delay_seconds=CONFIRMATION_DELETE_DELAY)

        for income in incomes:
            category_name = income.category.name if income.category else "без категории"
            await notify_group_about_income(bot, user, category_name, f"{income.amount:.0f}")

        for income in incomes:
            if (income.description or "").strip() != "Без описания":
                await prompt_unknown_category(bot, message.chat.id, income.description or "")
        return

    # ─── Расход ────────────────────────────────────────
    items = ExpenseParser.parse(text)
    if not items:
        await tool_box.cleaner.delete_user_message(message)
        await send_temporary(bot, message.chat.id, t("expense.parse_error"))
        return

    created_expenses = await ExpenseService.create_from_message(user, message)
    await tool_box.cleaner.delete_user_message(message)

    if not created_expenses:
        await send_temporary(bot, message.chat.id, t("expense.save_error"))
        return

    if len(created_expenses) == 1:
        expense = created_expenses[0]
        category_name = expense.category.name if expense.category else "без категории"
        confirmation = t("expense.confirmed_single", category=category_name, amount=f"{expense.amount:.0f}")
    else:
        lines = [t("expense.confirmed_multi", count=str(len(created_expenses)))]
        for expense in created_expenses:
            category_name = expense.category.name if expense.category else "без категории"
            lines.append(f"  • {category_name} — {expense.amount:.0f} ₽")
        confirmation = "\n".join(lines)

    await send_temporary(bot, message.chat.id, confirmation, delay_seconds=CONFIRMATION_DELETE_DELAY)

    for expense in created_expenses:
        category_name = expense.category.name if expense.category else "без категории"
        await notify_group_about_expense(bot, user, category_name, f"{expense.amount:.0f}")

    for amount, category_text in items:
        await prompt_unknown_category(bot, message.chat.id, category_text)


# ─── Обработчики кнопок категорий ─────────────────────

@expenses.callback_query(CategoryAction.filter(F.action == CAT_ADD_NEW))
async def category_add_new(callback: types.CallbackQuery, callback_data: CategoryAction):
    text = callback.message.text or ""
    category_name = _extract_category_name(text)
    if category_name:
        category = await CategoryService.create_category(category_name)
        await callback.message.edit_text(t("category.created", name=category.name))
        await asyncio.sleep(3)
        try:
            await callback.message.delete()
        except Exception:
            pass
    else:
        await callback.answer(t("error.category_name_failed"), show_alert=True)
    await callback.answer()


@expenses.callback_query(CategoryAction.filter(F.action == CAT_ADD_ALIAS))
async def category_add_alias(callback: types.CallbackQuery, callback_data: CategoryAction):
    text = callback.message.text or ""
    alias_name = _extract_category_name(text)
    if alias_name and callback_data.category_id:
        from project.apps.expenses.models import Category
        category = await Category.objects.filter(id=callback_data.category_id).afirst()
        if category:
            await CategoryService.add_alias(category, alias_name)
            await callback.message.edit_text(t("category.alias_added", alias=alias_name, category=category.name))
            await asyncio.sleep(3)
            try:
                await callback.message.delete()
            except Exception:
                pass
            await callback.answer()
            return
    await callback.answer(t("error.alias_failed"), show_alert=True)


@expenses.callback_query(CategoryAction.filter(F.action == CAT_USE_OTHER))
async def category_use_other(callback: types.CallbackQuery, callback_data: CategoryAction):
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.answer(t("category.kept_other"))


def _extract_category_name(bot_message_text: str) -> str | None:
    if "«" in bot_message_text and "»" in bot_message_text:
        start = bot_message_text.index("«") + 1
        end = bot_message_text.index("»")
        return bot_message_text[start:end].strip()
    return None
