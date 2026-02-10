from decimal import Decimal

from django.db import models
from django.conf import settings

from project.apps.core.models.base_model_mixin import BaseModelMixin


class SavingGoal(BaseModelMixin):
    """Цель накопления. Пользователь задает целевую сумму и (опционально)
    дедлайн. Прогресс обновляется при внесении пополнений."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="saving_goals",
        verbose_name="Пользователь",
    )
    name = models.CharField(
        max_length=200,
        verbose_name="Название цели",
    )
    target_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Целевая сумма",
    )
    current_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="Накоплено",
    )
    deadline = models.DateField(
        null=True,
        blank=True,
        verbose_name="Дедлайн",
    )
    is_achieved = models.BooleanField(
        default=False,
        verbose_name="Достигнута",
    )

    class Meta:
        verbose_name = "Цель накопления"
        verbose_name_plural = "Цели накоплений"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_achieved"]),
        ]

    @property
    def progress_percent(self) -> Decimal:
        if self.target_amount <= 0:
            return Decimal("100.00")
        return (self.current_amount / self.target_amount * 100).quantize(
            Decimal("0.01")
        )

    @property
    def remaining(self) -> Decimal:
        return max(self.target_amount - self.current_amount, Decimal("0.00"))

    def __str__(self):
        return f"{self.name}: {self.current_amount}/{self.target_amount} ₽ ({self.progress_percent}%)"
