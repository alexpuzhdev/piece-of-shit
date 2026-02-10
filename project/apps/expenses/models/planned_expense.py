from django.db import models
from django.conf import settings

from project.apps.core.models.base_model_mixin import BaseModelMixin


class PlannedExpense(BaseModelMixin):
    """Плановая (будущая) трата — например, ТО машины в июне 2026.
    Учитывается в прогнозе бюджета, но не является фактическим расходом
    до тех пор, пока пользователь не подтвердит списание."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="planned_expenses",
        verbose_name="Пользователь",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма",
    )
    category = models.ForeignKey(
        "expenses.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="planned_expenses",
        verbose_name="Категория",
    )
    description = models.CharField(
        max_length=255,
        verbose_name="Описание",
    )
    planned_date = models.DateField(
        verbose_name="Планируемая дата",
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name="Выполнено",
    )
    linked_expense = models.OneToOneField(
        "expenses.Expense",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="planned_source",
        verbose_name="Связанный расход",
    )

    class Meta:
        verbose_name = "Плановая трата"
        verbose_name_plural = "Плановые траты"
        ordering = ["planned_date"]
        indexes = [
            models.Index(fields=["user", "planned_date"]),
            models.Index(fields=["is_completed"]),
        ]

    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f"[{status}] {self.description}: {self.amount} ₽ на {self.planned_date}"
