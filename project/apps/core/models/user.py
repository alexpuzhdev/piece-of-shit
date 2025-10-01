from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    tg_id = models.BigIntegerField(
        verbose_name="Telegram ID",
        unique=True,
        null=False,
        blank=False,
    )

    username = models.CharField(
        verbose_name="username",
        max_length=255,
        null=True,
        unique=True,
        blank=True,
    )

    first_name = models.CharField(
        verbose_name="Имя",
        max_length=255,
        null=True,
        blank=True,
    )

    last_name = models.CharField(
        verbose_name="Фамилия",
        max_length=255,
        null=True,
        blank=True,
    )

    is_bot = models.BooleanField(
        verbose_name="Это бот",
        default=False,
    )

    language_code = models.CharField(
        verbose_name="Язык Telegram",
        max_length=10,
        null=True,
        blank=True,
    )

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.username or f"tg:{self.tg_id}"
