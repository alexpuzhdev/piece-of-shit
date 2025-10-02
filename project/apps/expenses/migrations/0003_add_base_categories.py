from django.db import migrations


def forwards_func(apps, schema_editor):
    Category = apps.get_model("expenses", "Category")
    CategoryAlias = apps.get_model("expenses", "CategoryAlias")

    data = {
        "Еда": [
            "Еда", "Перекус", "Перекусик", "Хавчик", "Обед", "Ужин", "Завтрак",
            "Продукты", "Продукты немножко", "Продукты из пятерки",
            "Чижик", "Пятерка", "Пятёрочка", "Бакалея", "Супермаркет", "Магазин",
            "Вода", "Минералка", "Хлеб", "Молочка", "Молоко", "Соки", "Напитки",
            "Кофе", "Чай", "Перекус в тц", "Доставка еды", "Самокат", "Яндекс еда", "Вкусвилл"
        ],
        "Транспорт": [
            "Проезд", "Автобус", "Маршрутка", "Метро", "Подземка", "Электричка",
            "Такси", "Яндекс такси", "Убер", "Болт", "Поездка", "Транспорт",
            "Каршеринг", "Парковка", "Бензин", "Топливо", "Заправка"
        ],
        "Развлечения": [
            "Кино", "Кинотеатр", "Билеты", "Билеты кино", "Поход в кино", "Фильм",
            "Попкорн", "Попкормовый", "Развлечения", "Концерт", "Шоу", "Театр",
            "Игра", "Игры", "Хоккей", "Спорт события", "Настолки"
        ],
        "Личное": [
            "Стрижка", "Барбер", "Парикмахер", "Салон", "Маникюр", "Педикюр",
            "Массаж", "Раскайфовка", "Уход", "Косметика", "Спорт",
            "Абонемент", "Тренировка", "Фитнес", "Зал", "Одежда", "Вещи"
        ],
        "Прочее": [
            "Штраф", "Штрафы", "Покупки", "Покупка", "Заказ", "Доставка",
            "Интернет", "Подписка", "Расходы", "Другое"
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
    CategoryAlias.objects.all().delete()
    Category.objects.all().delete()


class Migration(migrations.Migration):
    dependencies = [
        ("expenses", "0002_categoryalias"),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
