import calendar
import logging
from datetime import date

from asgiref.sync import sync_to_async

from project.apps.expenses.models import IncomeSchedule, PlannedExpense


logger = logging.getLogger(__name__)


class ReminderService:
    """Сервис проверки расписаний доходов и предстоящих плановых трат.
    Предназначен для ежедневного запуска (через aiogram scheduler или cron)."""

    @staticmethod
    @sync_to_async
    def get_todays_income_reminders() -> list[IncomeSchedule]:
        """Возвращает расписания, у которых сегодня день начисления."""
        today = date.today()
        day = today.day

        # Обработка «31-е число в месяце с 30 днями» и т.д.
        last_day_of_month = calendar.monthrange(today.year, today.month)[1]

        schedules = list(
            IncomeSchedule.objects.filter(
                is_active=True,
                deleted_at__isnull=True,
            )
            .select_related("user")
        )

        result = []
        for schedule in schedules:
            trigger_day = min(schedule.day_of_month, last_day_of_month)
            if trigger_day == day:
                result.append(schedule)

        return result

    @staticmethod
    @sync_to_async
    def get_todays_planned_expense_reminders() -> list[PlannedExpense]:
        """Возвращает плановые траты, запланированные на сегодня."""
        today = date.today()
        return list(
            PlannedExpense.objects.filter(
                planned_date=today,
                is_completed=False,
                deleted_at__isnull=True,
            )
            .select_related("user", "category")
        )

    @staticmethod
    @sync_to_async
    def get_upcoming_planned_expenses(days_ahead: int = 3) -> list[PlannedExpense]:
        """Возвращает плановые траты в ближайшие N дней."""
        from datetime import timedelta

        today = date.today()
        end_date = today + timedelta(days=days_ahead)

        return list(
            PlannedExpense.objects.filter(
                planned_date__gte=today,
                planned_date__lte=end_date,
                is_completed=False,
                deleted_at__isnull=True,
            )
            .select_related("user", "category")
            .order_by("planned_date")
        )

    @staticmethod
    def format_income_reminder(schedule: IncomeSchedule) -> str:
        amount_text = f" ({schedule.expected_amount:.0f} ₽)" if schedule.expected_amount else ""
        return (
            f"🔔 Сегодня день начисления: <b>{schedule.name}</b>{amount_text}\n"
            f"Не забудьте внести данные о доходе!"
        )

    @staticmethod
    def format_planned_expense_reminder(planned: PlannedExpense) -> str:
        category_text = f" | {planned.category.name}" if planned.category else ""
        return (
            f"📋 Плановая трата на сегодня: <b>{planned.description}</b> "
            f"— {planned.amount:.0f} ₽{category_text}"
        )
