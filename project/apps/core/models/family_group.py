from django.db import models
from django.conf import settings

from project.apps.core.models.base_model_mixin import BaseModelMixin


class FamilyGroup(BaseModelMixin):
    """Семейная группа. Пользователи одной группы могут
    видеть отчёты друг друга."""

    name = models.CharField(
        max_length=100,
        verbose_name="Название группы",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="created_family_groups",
        verbose_name="Создатель",
    )
    invite_code = models.CharField(
        max_length=20,
        unique=True,
        verbose_name="Код приглашения",
        help_text="Уникальный код для присоединения к группе",
    )

    class Meta:
        verbose_name = "Семейная группа"
        verbose_name_plural = "Семейные группы"
        ordering = ["-created_at"]

    def __str__(self):
        return self.name


class FamilyGroupMembership(BaseModelMixin):
    """Членство пользователя в семейной группе."""

    ROLE_ADMIN = "admin"
    ROLE_MEMBER = "member"
    ROLE_CHOICES = (
        (ROLE_ADMIN, "Администратор"),
        (ROLE_MEMBER, "Участник"),
    )

    group = models.ForeignKey(
        FamilyGroup,
        on_delete=models.CASCADE,
        related_name="memberships",
        verbose_name="Группа",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="family_memberships",
        verbose_name="Пользователь",
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default=ROLE_MEMBER,
        verbose_name="Роль",
    )
    notifications_enabled = models.BooleanField(
        default=True,
        verbose_name="Уведомления включены",
        help_text="Получать уведомления о расходах/доходах других участников группы",
    )

    class Meta:
        verbose_name = "Участник группы"
        verbose_name_plural = "Участники групп"
        constraints = [
            models.UniqueConstraint(
                fields=["group", "user"],
                name="unique_membership_per_group_user",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "group"]),
        ]

    def __str__(self):
        return f"{self.user} → {self.group.name} ({self.role})"
