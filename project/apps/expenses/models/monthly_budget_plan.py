from decimal import Decimal

from django.db import models
from django.conf import settings

from project.apps.core.models.base_model_mixin import BaseModelMixin


class MonthlyBudgetPlan(BaseModelMixin):
    """Бюджетный план на конкретный месяц. Создаётся на основе
    общего шаблона Budget, но может содержать индивидуальные
    корректировки (отпуск, перенос остатка, разовые расходы).

    carry_over — остаток с предыдущего месяца. Применяется
    ТОЛЬКО по подтверждению пользователя (не автоматически)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="monthly_budget_plans",
        verbose_name="Пользователь",
    )
    month = models.DateField(
        verbose_name="Месяц",
        help_text="Первое число месяца (например, 2026-02-01)",
    )
    category = models.ForeignKey(
        "expenses.Category",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="monthly_plans",
        verbose_name="Категория",
        help_text="NULL = общий бюджет",
    )
    planned_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Запланированный лимит",
    )
    carry_over = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Перенос с прошлого месяца",
    )
    carry_over_applied = models.BooleanField(
        default=False,
        verbose_name="Перенос подтверждён",
    )

    class Meta:
        verbose_name = "Месячный бюджетный план"
        verbose_name_plural = "Месячные бюджетные планы"
        ordering = ["-month", "category"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "month", "category"],
                name="unique_monthly_plan_per_user_category",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "month"]),
        ]

    @property
    def effective_limit(self) -> Decimal:
        """Итоговый лимит с учётом подтверждённого переноса."""
        if self.carry_over_applied:
            return self.planned_limit + self.carry_over
        return self.planned_limit

    def __str__(self):
        category_label = self.category or "Общий"
        return f"{self.month:%Y-%m} | {category_label}: {self.effective_limit} ₽"
