from django.db import migrations


def forwards_func(apps, schema_editor):
    Category = apps.get_model("expenses", "Category")
    CategoryAlias = apps.get_model("expenses", "CategoryAlias")
    Expense = apps.get_model("expenses", "Expense")

    try:
        it_category = Category.objects.get(name="IT и цифровые сервисы")
        subscriptions = Category.objects.get(name="Подписки")
    except Category.DoesNotExist:
        return

    CategoryAlias.objects.filter(category=it_category).update(category=subscriptions)

    Expense.objects.filter(category=it_category).update(category=subscriptions)

    it_category.delete()

    new_aliases = [
        "Прокси", "VPN", "Впн", "Хостинг", "Сервер", "Cloud", "Облако",
        "Домен", "GitHub", "Git", "Gitlab", "Google Drive", "Google One",
        "iCloud", "Mega", "Dropbox",

        "Нетфликс", "Netflix", "Спотифай", "Spotify", "Ютуб", "Youtube",
        "Кинопоиск", "КиноПоиск Hd", "Окко", "Okko", "Иви", "Ivi",
        "Wink", "Амедиатека", "Amediateka", "Apple Music", "Яндекс Музыка",
        "Yandex Music", "Tidal", "Deezer", "Amazon Prime", "Hbo", "Hbo Max",
        "Disney+", "Дисней+", "Paramount+", "Парамонт+",
    ]

    objs = [CategoryAlias(category=subscriptions, alias=a.title()) for a in new_aliases]
    CategoryAlias.objects.bulk_create(objs, ignore_conflicts=True)


def reverse_func(apps, schema_editor):
    Category = apps.get_model("expenses", "Category")
    CategoryAlias = apps.get_model("expenses", "CategoryAlias")

    it_category, _ = Category.objects.get_or_create(name="IT и цифровые сервисы")

    to_delete = [
        "Прокси", "Vpn", "Впн", "Хостинг", "Сервер", "Cloud", "Облако",
        "Домен", "Github", "Git", "Gitlab", "Google Drive", "Google One",
        "Icloud", "Mega", "Dropbox",
        "Нетфликс", "Netflix", "Спотифай", "Spotify", "Ютуб", "Youtube",
        "Кинопоиск", "Кинопоиск Hd", "Окко", "Okko", "Иви", "Ivi",
        "Wink", "Амедиатека", "Amediateka", "Apple Music", "Яндекс Музыка",
        "Yandex Music", "Tidal", "Deezer", "Amazon Prime", "Hbo", "Hbo Max",
        "Disney+", "Дисней+", "Paramount+", "Парамонт+",
    ]

    CategoryAlias.objects.filter(alias__in=to_delete).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("expenses", "0009_add_more_realistic_aliases_and_categories"),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
    ]
