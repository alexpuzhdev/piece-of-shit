from django.conf import settings
from django.db import models

from project.apps.core.models.base_model_mixin import BaseModelMixin


class Feedback(BaseModelMixin):
    """Обратная связь из бота (просмотр только в админке)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="feedback_entries",
        verbose_name="Пользователь",
    )
    text = models.TextField(
        verbose_name="Текст",
    )
    chat_id = models.BigIntegerField(
        verbose_name="Chat ID",
        null=True,
        blank=True,
        db_index=True,
    )

    class Meta:
        verbose_name = "Обратная связь"
        verbose_name_plural = "Обратная связь"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.created_at:%Y-%m-%d %H:%M}"
