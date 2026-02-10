from decimal import Decimal

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError

from project.apps.core.models.base_model_mixin import BaseModelMixin


class VacationPeriod(BaseModelMixin):
    """Период отпуска. Используется при планировании бюджета:
    в месяцы с отпуском бюджет может корректироваться (например,
    увеличиваться на множитель budget_multiplier)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vacation_periods",
        verbose_name="Пользователь",
    )
    start_date = models.DateField(
        verbose_name="Начало отпуска",
    )
    end_date = models.DateField(
        verbose_name="Конец отпуска",
    )
    budget_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=Decimal("1.50"),
        verbose_name="Множитель бюджета",
        help_text="Во сколько раз увеличить лимит бюджета на период отпуска",
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Описание",
    )

    class Meta:
        verbose_name = "Период отпуска"
        verbose_name_plural = "Периоды отпусков"
        ordering = ["start_date"]
        indexes = [
            models.Index(fields=["user", "start_date", "end_date"]),
        ]

    def clean(self):
        super().clean()
        if self.start_date and self.end_date and self.start_date > self.end_date:
            raise ValidationError(
                {"end_date": "Дата окончания не может быть раньше даты начала."}
            )

    def __str__(self):
        return f"Отпуск {self.start_date} — {self.end_date} (×{self.budget_multiplier})"
