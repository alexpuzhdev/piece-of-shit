from datetime import date
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.db.models import Sum

from project.apps.core.models import User
from project.apps.expenses.models import PlannedExpense, Expense, Category
from project.apps.expenses.services.category_service import CategoryService


class PlannedExpenseService:
    """Управление плановыми (будущими) тратами."""

    @staticmethod
    @sync_to_async
    def create(
        user: User,
        amount: Decimal,
        description: str,
        planned_date: date,
        category_name: str | None = None,
    ) -> PlannedExpense:
        category = None
        if category_name:
            from project.apps.expenses.services.category_service import CategoryService
            # CategoryService.get_or_create — async, но тут sync_to_async-обёртка
            # Поэтому вызываем синхронно через ORM напрямую
            from project.apps.expenses.models import Category as CategoryModel, CategoryAlias
            normalized = category_name.strip().title()
            category = CategoryModel.objects.filter(name__iexact=normalized).first()
            if not category:
                alias = CategoryAlias.objects.filter(
                    alias__iexact=normalized
                ).select_related("category").first()
                if alias:
                    category = alias.category

        return PlannedExpense.objects.create(
            user=user,
            amount=abs(amount),
            description=description,
            planned_date=planned_date,
            category=category,
        )

    @staticmethod
    @sync_to_async
    def get_upcoming(user: User, limit: int = 10) -> list[PlannedExpense]:
        """Возвращает предстоящие плановые траты."""
        return list(
            PlannedExpense.objects.filter(
                user=user,
                is_completed=False,
                planned_date__gte=date.today(),
                deleted_at__isnull=True,
            )
            .select_related("category")
            .order_by("planned_date")[:limit]
        )

    @staticmethod
    @sync_to_async
    def get_overdue(user: User) -> list[PlannedExpense]:
        """Возвращает просроченные плановые траты."""
        return list(
            PlannedExpense.objects.filter(
                user=user,
                is_completed=False,
                planned_date__lt=date.today(),
                deleted_at__isnull=True,
            )
            .select_related("category")
            .order_by("planned_date")
        )

    @staticmethod
    @sync_to_async
    def complete(planned: PlannedExpense, actual_expense: Expense | None = None) -> PlannedExpense:
        """Помечает плановую трату как выполненную."""
        planned.is_completed = True
        update_fields = ["is_completed", "updated_at"]

        if actual_expense:
            planned.linked_expense = actual_expense
            update_fields.append("linked_expense")

        planned.save(update_fields=update_fields)
        return planned

    @staticmethod
    @sync_to_async
    def get_total_planned_for_month(
        user: User,
        month: date,
    ) -> Decimal:
        """Сумма плановых трат на указанный месяц."""
        from calendar import monthrange

        month_first = month.replace(day=1)
        last_day = monthrange(month_first.year, month_first.month)[1]
        month_end = month_first.replace(day=last_day)

        result = PlannedExpense.objects.filter(
            user=user,
            is_completed=False,
            planned_date__gte=month_first,
            planned_date__lte=month_end,
            deleted_at__isnull=True,
        ).aggregate(total=Sum("amount"))

        return result["total"] or Decimal("0.00")

    @staticmethod
    def format_planned(planned: PlannedExpense) -> str:
        """Форматирует плановую трату для отображения в Telegram."""
        category_label = planned.category.name if planned.category else ""
        status = "✅" if planned.is_completed else "📋"
        overdue = ""

        if not planned.is_completed and planned.planned_date < date.today():
            overdue = " ⏰ просрочено!"

        return (
            f"{status} <b>{planned.description}</b> — {planned.amount:.0f} ₽\n"
            f"   📅 {planned.planned_date}"
            f"{f' | {category_label}' if category_label else ''}"
            f"{overdue}"
        )
