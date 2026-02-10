from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_familygroupmembership_notifications_enabled"),
    ]

    operations = [
        migrations.CreateModel(
            name="BotText",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Создано")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Обновлено")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Удалено")),
                ("key", models.CharField(db_index=True, help_text="Уникальный идентификатор текста (например: menu.main.title)", max_length=150, unique=True, verbose_name="Ключ")),
                ("value", models.TextField(help_text="Поддерживает HTML-разметку Telegram и {placeholders}", verbose_name="Текст")),
                ("category", models.CharField(choices=[("message", "Сообщение"), ("button", "Кнопка"), ("error", "Ошибка"), ("confirmation", "Подтверждение"), ("notification", "Уведомление")], default="message", max_length=20, verbose_name="Тип")),
                ("description", models.CharField(blank=True, default="", help_text="Где используется этот текст", max_length=255, verbose_name="Описание")),
            ],
            options={
                "verbose_name": "Текст бота",
                "verbose_name_plural": "Тексты бота",
                "ordering": ["key"],
            },
        ),
    ]
