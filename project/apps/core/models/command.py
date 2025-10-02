from __future__ import annotations

from django.db import models

from project.apps.core.models.base_model_mixin import BaseModelMixin
from project.apps.core.utils.text import normalize_command_text

__all__ = [
    "Command",
    "CommandAlias",
]


class Command(BaseModelMixin):
    code = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Код",
    )
    name = models.CharField(
        max_length=150,
        verbose_name="Название",
    )
    description = models.TextField(
        blank=True,
        verbose_name="Описание",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Активна",
    )

    class Meta:
        verbose_name = "Команда"
        verbose_name_plural = "Команды"
        ordering = ["code"]

    def __str__(self) -> str:
        return self.name or self.code


class CommandAlias(BaseModelMixin):
    command = models.ForeignKey(
        Command,
        on_delete=models.CASCADE,
        related_name="aliases",
        verbose_name="Команда",
    )
    alias = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Триггер",
    )
    normalized_alias = models.CharField(
        max_length=150,
        unique=True,
        editable=False,
        verbose_name="Нормализованный триггер",
    )

    class Meta:
        verbose_name = "Алиас команды"
        verbose_name_plural = "Алиасы команд"
        ordering = ["alias"]
        indexes = [
            models.Index(fields=["normalized_alias"]),
        ]

    def __str__(self) -> str:
        return f"{self.alias} → {self.command.code}"

    def save(self, *args, **kwargs):
        self.normalized_alias = normalize_command_text(self.alias)
        super().save(*args, **kwargs)
