from django.contrib import admin

from project.apps.core.models import User, FamilyGroup, FamilyGroupMembership, BotText, Feedback


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "tg_id",
        "is_superuser",
        "is_staff",
        "username",
        "is_bot",
        "language_code",
    )
    list_filter = ("username", "is_bot", "is_staff")
    search_fields = ("username", "tg_id")


@admin.register(FamilyGroup)
class FamilyGroupAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_by", "invite_code", "created_at")
    search_fields = ("name", "invite_code")


@admin.register(FamilyGroupMembership)
class FamilyGroupMembershipAdmin(admin.ModelAdmin):
    list_display = ("id", "group", "user", "role", "notifications_enabled", "created_at")
    list_filter = ("role", "group", "notifications_enabled")


@admin.register(BotText)
class BotTextAdmin(admin.ModelAdmin):
    list_display = ("key", "category", "description", "updated_at")
    list_filter = ("category",)
    search_fields = ("key", "value", "description")
    ordering = ("key",)
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        (None, {
            "fields": ("key", "category", "description"),
        }),
        ("Содержимое", {
            "fields": ("value",),
            "description": "HTML-разметка Telegram. Используйте {placeholders} для динамических значений.",
        }),
        ("Даты", {
            "fields": ("created_at", "updated_at"),
        }),
    )


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "chat_id", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "text", "chat_id")
    readonly_fields = ("created_at", "updated_at")
