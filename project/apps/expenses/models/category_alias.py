from django.db import models

from project.apps.core.models.base_model_mixin import BaseModelMixin


class CategoryAlias(BaseModelMixin):
    category = models.ForeignKey(
        "expenses.Category",
        on_delete=models.CASCADE,
        related_name="aliases",
        verbose_name="Категория",
    )
    alias = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Альтернативное название",
    )

    class Meta:
        verbose_name = "Алиас категории"
        verbose_name_plural = "Алиасы категорий"
        ordering = ["alias"]
        indexes = [
            models.Index(fields=["alias"]),
        ]

    def __str__(self):
        return f"{self.alias} → {self.category.name}"
