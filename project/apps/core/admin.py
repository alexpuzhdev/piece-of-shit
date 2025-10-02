from django.contrib import admin

from project.apps.core.models import Command, CommandAlias, User


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


@admin.register(Command)
class CommandAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "code",
        "name",
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = ("code", "name", "description")


@admin.register(CommandAlias)
class CommandAliasAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "command",
        "alias",
        "normalized_alias",
    )
    search_fields = ("alias", "normalized_alias", "command__code", "command__name")
    autocomplete_fields = ("command",)
