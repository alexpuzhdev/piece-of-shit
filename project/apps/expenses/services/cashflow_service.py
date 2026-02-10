from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.db.models import Sum
from django.db.models.functions import Abs, TruncMonth

from project.apps.core.models import User
from project.apps.expenses.models import Expense, Income


@dataclass(frozen=True)
class CashflowSummary:
    """Итог cashflow за период."""
    total_income: Decimal
    total_expense: Decimal

    @property
    def net(self) -> Decimal:
        return self.total_income - self.total_expense

    @property
    def savings_rate_percent(self) -> Decimal:
        """Процент сбережений (доля неизрасходованного дохода)."""
        if self.total_income <= 0:
            return Decimal("0.00")
        return (self.net / self.total_income * 100).quantize(Decimal("0.01"))


@dataclass(frozen=True)
class MonthlyCashflowRow:
    """Cashflow за один месяц."""
    month: date
    income: Decimal
    expense: Decimal

    @property
    def net(self) -> Decimal:
        return self.income - self.expense


class CashflowService:
    """Сервис для расчёта cashflow (доходы − расходы)."""

    @staticmethod
    @sync_to_async
    def get_summary(
        user: User,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> CashflowSummary:
        income_queryset = Income.objects.filter(user=user, deleted_at__isnull=True)
        expense_queryset = Expense.objects.filter(user=user, deleted_at__isnull=True)

        if date_from:
            income_queryset = income_queryset.filter(created_at__date__gte=date_from)
            expense_queryset = expense_queryset.filter(created_at__date__gte=date_from)
        if date_to:
            income_queryset = income_queryset.filter(created_at__date__lte=date_to)
            expense_queryset = expense_queryset.filter(created_at__date__lte=date_to)

        total_income = income_queryset.aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")

        total_expense = expense_queryset.aggregate(
            total=Sum(Abs("amount"))
        )["total"] or Decimal("0.00")

        return CashflowSummary(
            total_income=total_income,
            total_expense=total_expense,
        )

    @staticmethod
    @sync_to_async
    def get_monthly_breakdown(
        user: User,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[MonthlyCashflowRow]:
        income_queryset = Income.objects.filter(user=user, deleted_at__isnull=True)
        expense_queryset = Expense.objects.filter(user=user, deleted_at__isnull=True)

        if date_from:
            income_queryset = income_queryset.filter(created_at__date__gte=date_from)
            expense_queryset = expense_queryset.filter(created_at__date__gte=date_from)
        if date_to:
            income_queryset = income_queryset.filter(created_at__date__lte=date_to)
            expense_queryset = expense_queryset.filter(created_at__date__lte=date_to)

        income_by_month = {
            row["month"]: row["total"]
            for row in income_queryset.annotate(
                month=TruncMonth("created_at")
            ).values("month").annotate(total=Sum("amount")).order_by("month")
        }

        expense_by_month = {
            row["month"]: row["total"]
            for row in expense_queryset.annotate(
                month=TruncMonth("created_at")
            ).values("month").annotate(total=Sum(Abs("amount"))).order_by("month")
        }

        all_months = sorted(set(income_by_month) | set(expense_by_month))

        return [
            MonthlyCashflowRow(
                month=month.date() if hasattr(month, "date") else month,
                income=income_by_month.get(month, Decimal("0.00")),
                expense=expense_by_month.get(month, Decimal("0.00")),
            )
            for month in all_months
        ]
