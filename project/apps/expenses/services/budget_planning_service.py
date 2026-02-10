from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.db.models import Sum
from django.db.models.functions import Abs

from project.apps.core.models import User
from project.apps.expenses.models import (
    Budget,
    Expense,
    MonthlyBudgetPlan,
    PlannedExpense,
    VacationPeriod,
    Category,
)


@dataclass(frozen=True)
class BudgetStatus:
    """Состояние бюджета: лимит, потрачено, остаток, рекомендация."""
    category_name: str | None
    limit: Decimal
    spent: Decimal
    planned_upcoming: Decimal

    @property
    def remaining(self) -> Decimal:
        return self.limit - self.spent

    @property
    def remaining_after_planned(self) -> Decimal:
        return self.limit - self.spent - self.planned_upcoming

    @property
    def overspent(self) -> bool:
        return self.spent > self.limit

    @property
    def usage_percent(self) -> Decimal:
        if self.limit <= 0:
            return Decimal("100.00")
        return (self.spent / self.limit * 100).quantize(Decimal("0.01"))


@dataclass(frozen=True)
class CarryOverProposal:
    """Предложение по переносу остатка бюджета в следующий месяц."""
    from_month: date
    to_month: date
    category_name: str | None
    carry_over_amount: Decimal


class BudgetPlanningService:
    """Сервис планирования бюджета: месячные планы, корректировки,
    рекомендации по перерасходу, перенос остатков."""

    @staticmethod
    @sync_to_async
    def get_or_create_monthly_plan(
        user: User,
        month: date,
        category: Category | None = None,
    ) -> MonthlyBudgetPlan:
        """Получает или создаёт месячный план на основе шаблона Budget."""
        month_first_day = month.replace(day=1)

        plan = MonthlyBudgetPlan.objects.filter(
            user=user,
            month=month_first_day,
            category=category,
            deleted_at__isnull=True,
        ).first()

        if plan:
            return plan

        # Ищем шаблон бюджета
        budget_template = Budget.objects.filter(
            user=user,
            category=category,
            deleted_at__isnull=True,
        ).first()

        base_limit = budget_template.limit if budget_template else Decimal("0.00")

        # Корректируем на отпуск
        adjusted_limit = BudgetPlanningService._apply_vacation_multiplier_sync(
            user, month_first_day, base_limit
        )

        return MonthlyBudgetPlan.objects.create(
            user=user,
            month=month_first_day,
            category=category,
            planned_limit=adjusted_limit,
        )

    @staticmethod
    def _apply_vacation_multiplier_sync(
        user: User,
        month_first_day: date,
        base_limit: Decimal,
    ) -> Decimal:
        """Применяет множитель отпуска, если в месяце есть отпускные дни."""
        from calendar import monthrange

        last_day = monthrange(month_first_day.year, month_first_day.month)[1]
        month_end = month_first_day.replace(day=last_day)

        vacation = VacationPeriod.objects.filter(
            user=user,
            start_date__lte=month_end,
            end_date__gte=month_first_day,
            deleted_at__isnull=True,
        ).first()

        if vacation:
            return (base_limit * vacation.budget_multiplier).quantize(Decimal("0.01"))

        return base_limit

    @staticmethod
    @sync_to_async
    def get_budget_status(
        user: User,
        month: date,
        category: Category | None = None,
    ) -> BudgetStatus | None:
        """Возвращает состояние бюджета за указанный месяц."""
        month_first_day = month.replace(day=1)
        from calendar import monthrange
        last_day = monthrange(month_first_day.year, month_first_day.month)[1]
        month_end = month_first_day.replace(day=last_day)

        plan = MonthlyBudgetPlan.objects.filter(
            user=user,
            month=month_first_day,
            category=category,
            deleted_at__isnull=True,
        ).first()

        if not plan:
            budget = Budget.objects.filter(
                user=user,
                category=category,
                deleted_at__isnull=True,
            ).first()
            if not budget:
                return None
            effective_limit = budget.limit
        else:
            effective_limit = plan.effective_limit

        # Считаем фактически потраченное
        expense_filter = {
            "user": user,
            "deleted_at__isnull": True,
            "created_at__date__gte": month_first_day,
            "created_at__date__lte": month_end,
        }
        if category:
            expense_filter["category"] = category

        spent = Expense.objects.filter(**expense_filter).aggregate(
            total=Sum(Abs("amount"))
        )["total"] or Decimal("0.00")

        # Считаем плановые траты до конца месяца
        planned_filter = {
            "user": user,
            "deleted_at__isnull": True,
            "is_completed": False,
            "planned_date__gte": date.today(),
            "planned_date__lte": month_end,
        }
        if category:
            planned_filter["category"] = category

        planned_upcoming = PlannedExpense.objects.filter(**planned_filter).aggregate(
            total=Sum("amount")
        )["total"] or Decimal("0.00")

        return BudgetStatus(
            category_name=category.name if category else None,
            limit=effective_limit,
            spent=spent,
            planned_upcoming=planned_upcoming,
        )

    @staticmethod
    @sync_to_async
    def calculate_carry_over(
        user: User,
        from_month: date,
        category: Category | None = None,
    ) -> CarryOverProposal | None:
        """Рассчитывает остаток бюджета для переноса в следующий месяц.
        Возвращает предложение (не применяет автоматически)."""
        from calendar import monthrange

        from_first = from_month.replace(day=1)
        last_day = monthrange(from_first.year, from_first.month)[1]
        from_end = from_first.replace(day=last_day)

        plan = MonthlyBudgetPlan.objects.filter(
            user=user,
            month=from_first,
            category=category,
            deleted_at__isnull=True,
        ).first()

        if not plan:
            return None

        spent = Expense.objects.filter(
            user=user,
            category=category if category else None,
            deleted_at__isnull=True,
            created_at__date__gte=from_first,
            created_at__date__lte=from_end,
        )
        if not category:
            spent = Expense.objects.filter(
                user=user,
                deleted_at__isnull=True,
                created_at__date__gte=from_first,
                created_at__date__lte=from_end,
            )

        total_spent = spent.aggregate(
            total=Sum(Abs("amount"))
        )["total"] or Decimal("0.00")

        carry_over = plan.effective_limit - total_spent

        if carry_over <= 0:
            return None

        # Следующий месяц
        if from_first.month == 12:
            to_month = from_first.replace(year=from_first.year + 1, month=1)
        else:
            to_month = from_first.replace(month=from_first.month + 1)

        return CarryOverProposal(
            from_month=from_first,
            to_month=to_month,
            category_name=category.name if category else None,
            carry_over_amount=carry_over,
        )

    @staticmethod
    @sync_to_async
    def apply_carry_over(
        user: User,
        to_month: date,
        carry_over_amount: Decimal,
        category: Category | None = None,
    ) -> MonthlyBudgetPlan:
        """Применяет перенос остатка к бюджету указанного месяца.
        Вызывается ТОЛЬКО по подтверждению пользователя."""
        month_first = to_month.replace(day=1)

        plan, _ = MonthlyBudgetPlan.objects.get_or_create(
            user=user,
            month=month_first,
            category=category,
            defaults={"planned_limit": Decimal("0.00")},
        )

        plan.carry_over = carry_over_amount
        plan.carry_over_applied = True
        plan.save(update_fields=["carry_over", "carry_over_applied", "updated_at"])

        return plan

    @staticmethod
    @sync_to_async
    def get_budget_recommendation(
        user: User,
        month: date,
    ) -> str | None:
        """Генерирует текстовую рекомендацию по корректировке бюджета,
        если траты отклоняются от плана."""
        from calendar import monthrange

        month_first = month.replace(day=1)
        last_day = monthrange(month_first.year, month_first.month)[1]
        month_end = month_first.replace(day=last_day)
        today = date.today()

        if today < month_first or today > month_end:
            return None

        days_in_month = last_day
        days_passed = (today - month_first).days + 1
        days_remaining = days_in_month - days_passed

        if days_remaining <= 0:
            return None

        plan = MonthlyBudgetPlan.objects.filter(
            user=user,
            month=month_first,
            category__isnull=True,
            deleted_at__isnull=True,
        ).first()

        if not plan:
            budget = Budget.objects.filter(
                user=user,
                category__isnull=True,
                deleted_at__isnull=True,
            ).first()
            if not budget:
                return None
            effective_limit = budget.limit
        else:
            effective_limit = plan.effective_limit

        total_spent = Expense.objects.filter(
            user=user,
            deleted_at__isnull=True,
            created_at__date__gte=month_first,
            created_at__date__lte=today,
        ).aggregate(
            total=Sum(Abs("amount"))
        )["total"] or Decimal("0.00")

        expected_pace = effective_limit / days_in_month * days_passed
        remaining_budget = effective_limit - total_spent
        daily_remaining = remaining_budget / days_remaining if days_remaining > 0 else Decimal("0")

        if total_spent > expected_pace * Decimal("1.15"):
            return (
                f"⚠️ Перерасход! Вы потратили {total_spent:.0f} ₽ за {days_passed} дн. "
                f"(план: {expected_pace:.0f} ₽).\n"
                f"До конца месяца осталось {remaining_budget:.0f} ₽ "
                f"— это ~{daily_remaining:.0f} ₽/день на {days_remaining} дн."
            )
        elif total_spent < expected_pace * Decimal("0.70"):
            return (
                f"✅ Хороший темп! Потрачено {total_spent:.0f} ₽ из {effective_limit:.0f} ₽. "
                f"Запас: ~{daily_remaining:.0f} ₽/день."
            )

        return None
