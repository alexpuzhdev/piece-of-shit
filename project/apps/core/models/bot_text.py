from django.db import models

from project.apps.core.models.base_model_mixin import BaseModelMixin


class BotText(BaseModelMixin):
    """Системная модель для управления текстами бота.

    Содержит все сообщения, надписи кнопок, ошибки и уведомления.
    Через Django Admin можно изменять тексты без редеплоя.
    Если запись отсутствует — используется значение по умолчанию из кода.
    """

    CATEGORY_MESSAGE = "message"
    CATEGORY_BUTTON = "button"
    CATEGORY_ERROR = "error"
    CATEGORY_CONFIRMATION = "confirmation"
    CATEGORY_NOTIFICATION = "notification"

    CATEGORY_CHOICES = (
        (CATEGORY_MESSAGE, "Сообщение"),
        (CATEGORY_BUTTON, "Кнопка"),
        (CATEGORY_ERROR, "Ошибка"),
        (CATEGORY_CONFIRMATION, "Подтверждение"),
        (CATEGORY_NOTIFICATION, "Уведомление"),
    )

    key = models.CharField(
        max_length=150,
        unique=True,
        db_index=True,
        verbose_name="Ключ",
        help_text="Уникальный идентификатор текста (например: menu.main.title)",
    )
    value = models.TextField(
        verbose_name="Текст",
        help_text="Поддерживает HTML-разметку Telegram и {placeholders}",
    )
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default=CATEGORY_MESSAGE,
        verbose_name="Тип",
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        default="",
        verbose_name="Описание",
        help_text="Где используется этот текст",
    )

    class Meta:
        verbose_name = "Текст бота"
        verbose_name_plural = "Тексты бота"
        ordering = ["key"]

    def __str__(self):
        return f"[{self.category}] {self.key}"
