from django.db import models
from django.conf import settings

from project.apps.core.models.base_model_mixin import BaseModelMixin


class Budget(BaseModelMixin):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="budgets",
        verbose_name="Пользователь",
    )
    category = models.ForeignKey(
        "expenses.Category",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="budgets",
        verbose_name="Категория",
    )
    limit = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Лимит",
    )
    currency = models.CharField(
        max_length=10,
        default="RUB",
        verbose_name="Валюта",
    )
    period = models.CharField(
        max_length=20,
        choices=(
            ("daily", "Ежедневный"),
            ("weekly", "Еженедельный"),
            ("monthly", "Ежемесячный"),
        ),
        default="monthly",
        verbose_name="Период",
    )

    class Meta:
        verbose_name = "Бюджет"
        verbose_name_plural = "Бюджеты"
        ordering = ["user", "category"]

    def __str__(self):
        if self.category:
            return f"{self.user}: {self.limit} {self.currency} на {self.category} ({self.period})"
        return f"{self.user}: {self.limit} {self.currency} (общий, {self.period})"