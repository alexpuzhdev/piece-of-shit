from django.contrib import admin

from project.apps.expenses.models import (
    Expense,
    Budget,
    Category,
    CategoryAlias,
    Income,
    PlannedExpense,
    SavingGoal,
    IncomeSchedule,
    VacationPeriod,
    MonthlyBudgetPlan,
)


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "amount",
        "category",
        "chat_id",
        "created_at",
    ]
    list_filter = ["category", "created_at"]
    search_fields = ["user__username", "category__name"]


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "category",
        "limit",
        "currency",
        "period",
    ]
    list_filter = ["period", "category"]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "name",
    ]
    search_fields = ["name"]


@admin.register(CategoryAlias)
class CategoryAliasAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "category",
        "alias",
    ]
    search_fields = ["alias", "category__name"]


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "amount",
        "category",
        "description",
        "chat_id",
        "created_at",
    ]
    list_filter = ["category", "created_at"]
    search_fields = ["user__username", "description"]


@admin.register(PlannedExpense)
class PlannedExpenseAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "amount",
        "description",
        "planned_date",
        "is_completed",
        "category",
    ]
    list_filter = ["is_completed", "planned_date", "category"]
    search_fields = ["description", "user__username"]


@admin.register(SavingGoal)
class SavingGoalAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "name",
        "target_amount",
        "current_amount",
        "deadline",
        "is_achieved",
    ]
    list_filter = ["is_achieved", "deadline"]
    search_fields = ["name", "user__username"]


@admin.register(IncomeSchedule)
class IncomeScheduleAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "name",
        "day_of_month",
        "expected_amount",
        "is_active",
    ]
    list_filter = ["is_active", "day_of_month"]


@admin.register(VacationPeriod)
class VacationPeriodAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "start_date",
        "end_date",
        "budget_multiplier",
        "description",
    ]
    list_filter = ["start_date", "end_date"]


@admin.register(MonthlyBudgetPlan)
class MonthlyBudgetPlanAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user",
        "month",
        "category",
        "planned_limit",
        "carry_over",
        "carry_over_applied",
    ]
    list_filter = ["month", "carry_over_applied", "category"]
