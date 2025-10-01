from django.contrib import admin

from project.apps.core.models import User


@admin.register(User)
class CoreAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tg_id",
        "is_superuser",
        "is_staff",
        "username",
        "is_bot",
        "language_code",
    )
    list_filter = (
        "username",
        "is_bot",
    )

