"""Добавляет модели FamilyGroup, FamilyGroupMembership
и создаёт базовые Django-группы (роли)."""

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


def create_django_groups(apps, schema_editor):
    """Создаёт базовые Django-группы для ролевой модели."""
    Group = apps.get_model("auth", "Group")
    for group_name in ("admin", "user", "family_admin"):
        Group.objects.get_or_create(name=group_name)


def reverse_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    Group.objects.filter(name__in=("admin", "user", "family_admin")).delete()


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0004_ad_password_for_user"),
    ]

    operations = [
        # ─── FamilyGroup ───────────────────────────────
        migrations.CreateModel(
            name="FamilyGroup",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата обновления")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата удаления")),
                ("add_attr", models.JSONField(blank=True, default=dict, verbose_name="Доп. данные")),
                ("name", models.CharField(max_length=100, verbose_name="Название группы")),
                ("invite_code", models.CharField(
                    help_text="Уникальный код для присоединения к группе",
                    max_length=20,
                    unique=True,
                    verbose_name="Код приглашения",
                )),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="created_family_groups",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Создатель",
                    ),
                ),
            ],
            options={
                "verbose_name": "Семейная группа",
                "verbose_name_plural": "Семейные группы",
                "ordering": ["-created_at"],
            },
        ),

        # ─── FamilyGroupMembership ─────────────────────
        migrations.CreateModel(
            name="FamilyGroupMembership",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата обновления")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата удаления")),
                ("add_attr", models.JSONField(blank=True, default=dict, verbose_name="Доп. данные")),
                ("role", models.CharField(
                    choices=[("admin", "Администратор"), ("member", "Участник")],
                    default="member",
                    max_length=20,
                    verbose_name="Роль",
                )),
                (
                    "group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="memberships",
                        to="core.familygroup",
                        verbose_name="Группа",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="family_memberships",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Участник группы",
                "verbose_name_plural": "Участники групп",
            },
        ),
        migrations.AddConstraint(
            model_name="familygroupmembership",
            constraint=models.UniqueConstraint(
                fields=("group", "user"),
                name="unique_membership_per_group_user",
            ),
        ),
        migrations.AddIndex(
            model_name="familygroupmembership",
            index=models.Index(fields=["user", "group"], name="core_fgm_user_group_idx"),
        ),

        # ─── Django groups (роли) ──────────────────────
        migrations.RunPython(create_django_groups, reverse_groups),
    ]
