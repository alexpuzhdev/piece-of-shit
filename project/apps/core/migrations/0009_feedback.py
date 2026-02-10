from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0008_safe_fgm_index"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Feedback",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата обновления")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата удаления")),
                ("add_attr", models.JSONField(blank=True, default=dict, verbose_name="Доп. данные")),
                ("text", models.TextField(verbose_name="Текст")),
                ("chat_id", models.BigIntegerField(blank=True, db_index=True, null=True, verbose_name="Chat ID")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="feedback_entries",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Обратная связь",
                "verbose_name_plural": "Обратная связь",
                "ordering": ["-created_at"],
            },
        ),
    ]
