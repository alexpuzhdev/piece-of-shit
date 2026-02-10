"""Централизованная система текстов бота.

Использование:
    from bot.core.texts import t

    text = t("menu.main.title")
    text = t("budget.set.success", amount="80000", verb="установлен")
"""

from bot.core.texts.registry import BotTextRegistry

# Удобный алиас для использования в хэндлерах
t = BotTextRegistry.get

__all__ = ["t", "BotTextRegistry"]
