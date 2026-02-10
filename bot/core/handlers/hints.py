"""Подсказки — всплывающие окна (callback.answer с show_alert) для каждого раздела."""

from aiogram import Router, types

from bot.core.callbacks.menu import HintAction
from bot.core.texts import t

hints_router = Router()

# Маппинг секций на ключи текстов
_HINT_KEYS = {
    "main_menu": "hint.main_menu",
    "reports": "hint.reports",
    "budget": "hint.budget",
    "goals": "hint.goals",
    "planned": "hint.planned",
    "settings": "hint.settings",
}


@hints_router.callback_query(HintAction.filter())
async def show_hint(callback: types.CallbackQuery, callback_data: HintAction):
    """Показывает всплывающую подсказку для выбранного раздела."""
    text_key = _HINT_KEYS.get(callback_data.section)
    if text_key:
        await callback.answer(t(text_key), show_alert=True)
    else:
        await callback.answer("Подсказка недоступна.", show_alert=True)
