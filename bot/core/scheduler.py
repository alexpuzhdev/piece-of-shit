import asyncio
import logging
from datetime import datetime, time

from aiogram import Bot

from project.apps.expenses.services.reminder_service import ReminderService

logger = logging.getLogger(__name__)

# Время ежедневной проверки напоминаний (UTC)
REMINDER_CHECK_HOUR = 7
REMINDER_CHECK_MINUTE = 0


async def run_daily_reminders(bot: Bot):
    """Фоновая задача: ежедневно проверяет расписания доходов
    и плановые траты, отправляет напоминания пользователям.

    Запускается при старте бота и работает бесконечно."""
    logger.info("Reminder scheduler started")

    while True:
        try:
            now = datetime.utcnow()
            target_time = datetime.combine(now.date(), time(REMINDER_CHECK_HOUR, REMINDER_CHECK_MINUTE))

            if now >= target_time:
                # Уже прошло время — ждём до завтра
                from datetime import timedelta
                target_time += timedelta(days=1)

            wait_seconds = (target_time - now).total_seconds()
            logger.info(f"Next reminder check in {wait_seconds:.0f}s at {target_time}")
            await asyncio.sleep(wait_seconds)

            await _send_reminders(bot)

        except asyncio.CancelledError:
            logger.info("Reminder scheduler cancelled")
            break
        except Exception:
            logger.exception("Error in reminder scheduler")
            # Ждём 60 секунд перед повторной попыткой
            await asyncio.sleep(60)


async def _send_reminders(bot: Bot):
    """Проверяет и отправляет все напоминания на сегодня."""
    # Напоминания о доходах
    income_schedules = await ReminderService.get_todays_income_reminders()
    for schedule in income_schedules:
        try:
            text = ReminderService.format_income_reminder(schedule)
            await bot.send_message(
                chat_id=schedule.user.tg_id,
                text=text,
            )
            logger.info(f"Sent income reminder to user {schedule.user.tg_id}: {schedule.name}")
        except Exception:
            logger.exception(f"Failed to send income reminder to {schedule.user.tg_id}")

    # Напоминания о плановых тратах
    planned_expenses = await ReminderService.get_todays_planned_expense_reminders()
    for planned in planned_expenses:
        try:
            text = ReminderService.format_planned_expense_reminder(planned)
            await bot.send_message(
                chat_id=planned.user.tg_id,
                text=text,
            )
            logger.info(f"Sent planned expense reminder to user {planned.user.tg_id}: {planned.description}")
        except Exception:
            logger.exception(f"Failed to send planned reminder to {planned.user.tg_id}")

    # Предстоящие плановые траты (за 3 дня)
    upcoming = await ReminderService.get_upcoming_planned_expenses(days_ahead=3)
    for planned in upcoming:
        # Не дублируем те, что на сегодня — они уже обработаны выше
        from datetime import date
        if planned.planned_date == date.today():
            continue
        try:
            days_left = (planned.planned_date - date.today()).days
            text = (
                f"📅 Через {days_left} дн.: <b>{planned.description}</b> "
                f"— {planned.amount:.0f} ₽"
            )
            await bot.send_message(
                chat_id=planned.user.tg_id,
                text=text,
            )
        except Exception:
            logger.exception(f"Failed to send upcoming reminder to {planned.user.tg_id}")

    total = len(income_schedules) + len(planned_expenses) + len(upcoming)
    logger.info(f"Daily reminders sent: {total} total")
