"""Восстанавливает индекс core_fgm_user_group_idx если его нет (например, после потери миграции).
Удаление через IF EXISTS не падает при отсутствии индекса; создание через IF NOT EXISTS — при наличии."""

from django.db import migrations


def ensure_fgm_index(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP INDEX IF EXISTS core_fgm_user_group_idx;")
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS core_fgm_user_group_idx
            ON core_familygroupmembership (user_id, group_id);
        """)


def noop_reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_bottext"),
    ]

    operations = [
        migrations.RunPython(ensure_fgm_index, noop_reverse),
    ]
