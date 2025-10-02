from __future__ import annotations

from datetime import datetime

from asgiref.sync import sync_to_async
from django.db.models import Q, Sum
from django.db.models.functions import Abs

from project.apps.expenses.models import Expense
from project.apps.expenses.services.periods import PeriodRange

class ReportService:
    @staticmethod
    def format_date(expense: Expense) -> str:
        raw_date = expense.add_attr.get("date")
        if raw_date:
            try:
                dt = datetime.fromisoformat(raw_date)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                return raw_date
        return expense.created_at.strftime("%Y-%m-%d")

    @staticmethod
    @sync_to_async
    def get_expenses_by_chat(chat_id: int, start: datetime | None = None, end: datetime | None = None):
        filter_condition = ReportService._build_filter(chat_id, start=start, end=end)
        return list(
            Expense.objects.filter(filter_condition)
            .select_related("category", "user")
            .order_by("created_at")
        )

    @staticmethod
    @sync_to_async
    def get_total_by_chat(
        chat_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> float:
        return ReportService.calculate_total(chat_id, start=start, end=end)

    @staticmethod
    @sync_to_async
    def get_category_summary(
        chat_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ):
        return ReportService.calculate_category_summary(chat_id, start=start, end=end)

    @staticmethod
    @sync_to_async
    def get_dynamics(
        chat_id: int,
        current_period: PeriodRange,
        previous_period: PeriodRange | None = None,
    ) -> dict:
        return ReportService.calculate_dynamics(
            chat_id,
            current_period=current_period,
            previous_period=previous_period,
        )

    @staticmethod
    def calculate_total(
        chat_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> float:
        result = (
            Expense.objects.filter(
                ReportService._build_filter(chat_id, start, end)
            ).aggregate(total=Sum(Abs("amount")))
        )
        return float(result["total"] or 0)

    @staticmethod
    def calculate_category_summary(
        chat_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ):
        qs = (
            Expense.objects.filter(
                ReportService._build_filter(chat_id, start, end)
            )
            .values("category__name")
            .annotate(total=Sum(Abs("amount")))
            .order_by("-total")
        )
        return [
            (row["category__name"] or "Без категории", float(row["total"]))
            for row in qs
        ]

    @staticmethod
    def calculate_dynamics(
        chat_id: int,
        current_period: PeriodRange,
        previous_period: PeriodRange | None = None,
    ) -> dict:
        if previous_period is None and current_period.start and current_period.end:
            delta = current_period.end - current_period.start
            previous_period = PeriodRange(
                start=current_period.start - delta,
                end=current_period.start,
                label="предыдущий период",
            )

        current_total = ReportService.calculate_total(
            chat_id,
            start=current_period.start,
            end=current_period.end,
        )
        previous_total = ReportService.calculate_total(
            chat_id,
            start=previous_period.start if previous_period else None,
            end=previous_period.end if previous_period else None,
        )

        return {
            "current": current_total,
            "previous": previous_total,
            "difference": current_total - previous_total,
        }

    @staticmethod
    def _build_filter(
        chat_id: int,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> Q:
        filter_condition = Q(chat_id=chat_id) | Q(add_attr__chat_id=chat_id)
        if start:
            filter_condition &= Q(created_at__gte=start)
        if end:
            filter_condition &= Q(created_at__lt=end)
        return filter_condition