"""Добавляет модели: Income, PlannedExpense, SavingGoal,
IncomeSchedule, VacationPeriod, MonthlyBudgetPlan."""

import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("expenses", "0011_expense_chat_id"),
    ]

    operations = [
        # ─── Income ─────────────────────────────────────
        migrations.CreateModel(
            name="Income",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата обновления")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата удаления")),
                ("add_attr", models.JSONField(blank=True, default=dict, verbose_name="Доп. данные")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Сумма")),
                ("description", models.CharField(blank=True, default="", max_length=255, verbose_name="Описание")),
                ("chat_id", models.BigIntegerField(blank=True, db_index=True, null=True, verbose_name="Chat ID")),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="incomes",
                        to="expenses.category",
                        verbose_name="Категория",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="incomes",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Доход",
                "verbose_name_plural": "Доходы",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="income",
            index=models.Index(fields=["user", "created_at"], name="expenses_in_user_id_created_idx"),
        ),
        migrations.AddIndex(
            model_name="income",
            index=models.Index(fields=["category", "created_at"], name="expenses_in_cat_id_created_idx"),
        ),

        # ─── PlannedExpense ─────────────────────────────
        migrations.CreateModel(
            name="PlannedExpense",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата обновления")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата удаления")),
                ("add_attr", models.JSONField(blank=True, default=dict, verbose_name="Доп. данные")),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10, verbose_name="Сумма")),
                ("description", models.CharField(max_length=255, verbose_name="Описание")),
                ("planned_date", models.DateField(verbose_name="Планируемая дата")),
                ("is_completed", models.BooleanField(default=False, verbose_name="Выполнено")),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="planned_expenses",
                        to="expenses.category",
                        verbose_name="Категория",
                    ),
                ),
                (
                    "linked_expense",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="planned_source",
                        to="expenses.expense",
                        verbose_name="Связанный расход",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="planned_expenses",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Плановая трата",
                "verbose_name_plural": "Плановые траты",
                "ordering": ["planned_date"],
            },
        ),
        migrations.AddIndex(
            model_name="plannedexpense",
            index=models.Index(fields=["user", "planned_date"], name="expenses_pe_user_planned_idx"),
        ),
        migrations.AddIndex(
            model_name="plannedexpense",
            index=models.Index(fields=["is_completed"], name="expenses_pe_completed_idx"),
        ),

        # ─── SavingGoal ────────────────────────────────
        migrations.CreateModel(
            name="SavingGoal",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата обновления")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата удаления")),
                ("add_attr", models.JSONField(blank=True, default=dict, verbose_name="Доп. данные")),
                ("name", models.CharField(max_length=200, verbose_name="Название цели")),
                ("target_amount", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Целевая сумма")),
                ("current_amount", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12, verbose_name="Накоплено")),
                ("deadline", models.DateField(blank=True, null=True, verbose_name="Дедлайн")),
                ("is_achieved", models.BooleanField(default=False, verbose_name="Достигнута")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="saving_goals",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Цель накопления",
                "verbose_name_plural": "Цели накоплений",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="savinggoal",
            index=models.Index(fields=["user", "is_achieved"], name="expenses_sg_user_achieved_idx"),
        ),

        # ─── IncomeSchedule ────────────────────────────
        migrations.CreateModel(
            name="IncomeSchedule",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата обновления")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата удаления")),
                ("add_attr", models.JSONField(blank=True, default=dict, verbose_name="Доп. данные")),
                ("name", models.CharField(help_text="Например: Зарплата, Аванс, Фриланс", max_length=100, verbose_name="Название")),
                ("day_of_month", models.PositiveSmallIntegerField(
                    help_text="Если указан 31-й, а в месяце 30 дней — напоминание придёт 30-го",
                    validators=[
                        django.core.validators.MinValueValidator(1),
                        django.core.validators.MaxValueValidator(31),
                    ],
                    verbose_name="День месяца",
                )),
                ("expected_amount", models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True, verbose_name="Ожидаемая сумма")),
                ("is_active", models.BooleanField(default=True, verbose_name="Активно")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="income_schedules",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Расписание дохода",
                "verbose_name_plural": "Расписания доходов",
                "ordering": ["day_of_month"],
            },
        ),
        migrations.AddIndex(
            model_name="incomeschedule",
            index=models.Index(fields=["user", "is_active"], name="expenses_is_user_active_idx"),
        ),
        migrations.AddIndex(
            model_name="incomeschedule",
            index=models.Index(fields=["day_of_month"], name="expenses_is_day_idx"),
        ),

        # ─── VacationPeriod ────────────────────────────
        migrations.CreateModel(
            name="VacationPeriod",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата обновления")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата удаления")),
                ("add_attr", models.JSONField(blank=True, default=dict, verbose_name="Доп. данные")),
                ("start_date", models.DateField(verbose_name="Начало отпуска")),
                ("end_date", models.DateField(verbose_name="Конец отпуска")),
                ("budget_multiplier", models.DecimalField(
                    decimal_places=2,
                    default=Decimal("1.50"),
                    help_text="Во сколько раз увеличить лимит бюджета на период отпуска",
                    max_digits=4,
                    verbose_name="Множитель бюджета",
                )),
                ("description", models.CharField(blank=True, default="", max_length=255, verbose_name="Описание")),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="vacation_periods",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Период отпуска",
                "verbose_name_plural": "Периоды отпусков",
                "ordering": ["start_date"],
            },
        ),
        migrations.AddIndex(
            model_name="vacationperiod",
            index=models.Index(fields=["user", "start_date", "end_date"], name="expenses_vp_user_dates_idx"),
        ),

        # ─── MonthlyBudgetPlan ─────────────────────────
        migrations.CreateModel(
            name="MonthlyBudgetPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="Дата обновления")),
                ("deleted_at", models.DateTimeField(blank=True, null=True, verbose_name="Дата удаления")),
                ("add_attr", models.JSONField(blank=True, default=dict, verbose_name="Доп. данные")),
                ("month", models.DateField(help_text="Первое число месяца (например, 2026-02-01)", verbose_name="Месяц")),
                ("planned_limit", models.DecimalField(decimal_places=2, max_digits=12, verbose_name="Запланированный лимит")),
                ("carry_over", models.DecimalField(decimal_places=2, default=Decimal("0.00"), max_digits=12, verbose_name="Перенос с прошлого месяца")),
                ("carry_over_applied", models.BooleanField(default=False, verbose_name="Перенос подтверждён")),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        help_text="NULL = общий бюджет",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="monthly_plans",
                        to="expenses.category",
                        verbose_name="Категория",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="monthly_budget_plans",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Пользователь",
                    ),
                ),
            ],
            options={
                "verbose_name": "Месячный бюджетный план",
                "verbose_name_plural": "Месячные бюджетные планы",
                "ordering": ["-month", "category"],
            },
        ),
        migrations.AddConstraint(
            model_name="monthlybudgetplan",
            constraint=models.UniqueConstraint(
                fields=("user", "month", "category"),
                name="unique_monthly_plan_per_user_category",
            ),
        ),
        migrations.AddIndex(
            model_name="monthlybudgetplan",
            index=models.Index(fields=["user", "month"], name="expenses_mbp_user_month_idx"),
        ),
    ]
