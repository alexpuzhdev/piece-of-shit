from django.contrib import admin

from project.apps.expenses.models import Expense, Budget, Category, CategoryAlias


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "amount",
        "category",
        "add_attr"
    ]


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "category",
        "limit",
        "currency",
        "period",
        "add_attr"
    ]


@admin.register(Category)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
        "add_attr"
    ]



@admin.register(CategoryAlias)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "category",
        "alias",
        "add_attr"

    ]
