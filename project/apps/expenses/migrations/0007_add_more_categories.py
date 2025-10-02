from django.db import migrations


def forwards_func(apps, schema_editor):
    Category = apps.get_model("expenses", "Category")
    CategoryAlias = apps.get_model("expenses", "CategoryAlias")

    data = {
        "Связь": [
            "Связь", "Мтс", "Билайн", "Теле2", "Йота", "Мегафон",
            "Мобильный", "Тариф", "Интернет", "Оплата связи", "Счёт за телефон"
        ],
        "Подписки": [
            "Подписка", "Нетфликс", "Netflix", "Spotify", "Спотифай",
            "Youtube", "Ютуб", "Кинопоиск", "Айтюнс", "Apple Music",
            "Yandex Music", "Подписка Лоховска"
        ],
        "Развлечения": [
            "Приколясы", "Прикол", "Попкорн", "Попкормовый", "Лудомания",
            "Ставки", "Игра", "Игры", "Развлечения", "Туса",
            "Бар", "Кальян"
        ],
    }

    categories = [Category(name=name) for name in data.keys()]
    Category.objects.bulk_create(categories, ignore_conflicts=True)

    existing_categories = {c.name: c for c in Category.objects.all()}

    aliases = []
    for category_name, alias_list in data.items():
        category = existing_categories.get(category_name)
        if category:
            aliases.extend(
                [CategoryAlias(category=category, alias=alias) for alias in alias_list]
            )

    CategoryAlias.objects.bulk_create(aliases, ignore_conflicts=True)


def reverse_func(apps, schema_editor):
    Category = apps.get_model("expenses", "Category")
    CategoryAlias = apps.get_model("expenses", "CategoryAlias")

    CategoryAlias.objects.filter(
        alias__in=[
            "Мтс", "Билайн", "Теле2", "Йота", "Мегафон", "Мобильный", "Тариф",
            "Интернет", "Оплата связи", "Счёт за телефон",
            "Подписка", "Нетфликс", "Netflix", "Spotify", "Спотифай",
            "Youtube", "Ютуб", "Кинопоиск", "Айтюнс", "Apple Music",
            "Yandex Music", "Подписка Лоховска",
            "Приколясы", "Прикол", "Попкорн", "Попкормовый", "Лудомания",
            "Ставки", "Игра", "Игры", "Развлечения", "Туса",
            "Бар", "Кальян"
        ]
    ).delete()

    Category.objects.filter(name__in=["Связь", "Подписки"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("expenses", "0006_budget_add_attr_category_add_attr_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
