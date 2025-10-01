from django.db import models

from project.apps.core.models.base_model_mixin import BaseModelMixin


class Category(BaseModelMixin):
    name = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="Название категории",
    )

    class Meta:
        verbose_name = "Категория"
        verbose_name_plural = "Категории"
        ordering = ["name"]

    def __str__(self):
        return self.name
