from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator

from project.apps.core.models.base_model_mixin import BaseModelMixin


class IncomeSchedule(BaseModelMixin):
    """Расписание поступления дохода (зарплата, аванс и т.д.).
    Используется для напоминаний в день начисления."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="income_schedules",
        verbose_name="Пользователь",
    )
    name = models.CharField(
        max_length=100,
        verbose_name="Название",
        help_text="Например: Зарплата, Аванс, Фриланс",
    )
    day_of_month = models.PositiveSmallIntegerField(
        verbose_name="День месяца",
        validators=[MinValueValidator(1), MaxValueValidator(31)],
        help_text="Если указан 31-й, а в месяце 30 дней — напоминание придёт 30-го",
    )
    expected_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Ожидаемая сумма",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активно",
    )

    class Meta:
        verbose_name = "Расписание дохода"
        verbose_name_plural = "Расписания доходов"
        ordering = ["day_of_month"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["day_of_month"]),
        ]

    def __str__(self):
        amount_label = f" ({self.expected_amount} ₽)" if self.expected_amount else ""
        return f"{self.name}: {self.day_of_month}-е число{amount_label}"
