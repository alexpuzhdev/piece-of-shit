from django.db import models
from django.conf import settings

from project.apps.core.models.base_model_mixin import BaseModelMixin


class Income(BaseModelMixin):
    """Доход пользователя. Хранится отдельно от расходов (Expense),
    чтобы избежать путаницы знаков и упростить аналитику."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="incomes",
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
        related_name="incomes",
        verbose_name="Категория",
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Описание",
    )
    chat_id = models.BigIntegerField(
        verbose_name="Chat ID",
        db_index=True,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "Доход"
        verbose_name_plural = "Доходы"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["category", "created_at"]),
        ]

    def __str__(self):
        category_label = self.category or "без категории"
        return f"{self.user}: +{self.amount} ₽ — {category_label}"
