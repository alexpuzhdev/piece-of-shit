"""Сервис групповых уведомлений.

Отправляет временные уведомления участникам группы о расходах/доходах.
"""

import asyncio
import logging

from aiogram import Bot

from bot.core.texts import t
from project.apps.core.services.family_group_service import FamilyGroupService

logger = logging.getLogger(__name__)

_NOTIFICATION_TTL_SECONDS = 15


async def notify_group_about_expense(bot: Bot, author, category_name: str, amount: str) -> None:
    text = t("notification.group_expense", author=_display_name(author), category=category_name, amount=amount)
    await _send_to_group_recipients(bot, author, text)


async def notify_group_about_income(bot: Bot, author, category_name: str, amount: str) -> None:
    text = t("notification.group_income", author=_display_name(author), category=category_name, amount=amount)
    await _send_to_group_recipients(bot, author, text)


def _display_name(user) -> str:
    return user.first_name or user.username or str(user.tg_id)


async def _send_to_group_recipients(bot: Bot, author, text: str) -> None:
    recipient_ids = await FamilyGroupService.get_notification_recipients(author)
    for tg_id in recipient_ids:
        await _send_temporary_notification(bot, tg_id, text)


async def _send_temporary_notification(bot: Bot, chat_id: int, text: str) -> None:
    try:
        message = await bot.send_message(chat_id=chat_id, text=text)
        asyncio.create_task(_delayed_delete(bot, chat_id, message.message_id))
    except Exception:
        logger.exception("Не удалось отправить уведомление в чат %s", chat_id)


async def _delayed_delete(bot: Bot, chat_id: int, message_id: int) -> None:
    await asyncio.sleep(_NOTIFICATION_TTL_SECONDS)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass
