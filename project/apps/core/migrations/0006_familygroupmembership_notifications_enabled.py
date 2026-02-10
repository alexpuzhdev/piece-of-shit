from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_familygroup_familygroupmembership_django_groups"),
    ]

    operations = [
        migrations.AddField(
            model_name="familygroupmembership",
            name="notifications_enabled",
            field=models.BooleanField(
                default=True,
                help_text="Получать уведомления о расходах/доходах других участников группы",
                verbose_name="Уведомления включены",
            ),
        ),
    ]
