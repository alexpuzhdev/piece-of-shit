from django.db import models
from django.conf import settings

from project.apps.core.models.base_model_mixin import BaseModelMixin


class Expense(BaseModelMixin):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="expenses",
        verbose_name="Пользователь",
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name="Сумма",
    )
    chat_id = models.BigIntegerField(
        verbose_name="Chat ID",
        db_index=True,
        null=True,
        blank=True,
    )

    category = models.ForeignKey(
        "expenses.Category",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="expenses",
        verbose_name="Категория",
    )

    class Meta:
        verbose_name = "Расход"
        verbose_name_plural = "Расходы"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["category", "created_at"]),
        ]

    def __str__(self):
        return f"{self.user}: {self.amount} ₽ — {self.category}"
