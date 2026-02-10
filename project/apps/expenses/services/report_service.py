from datetime import date, datetime
from decimal import Decimal

from asgiref.sync import sync_to_async
from django.db.models import Q, Sum
from django.db.models.functions import Abs

from project.apps.expenses.models import Expense, Income


class ReportService:
    """Сервис отчётов: расходы, доходы, по категориям, по периоду."""

    # ─── Расходы ───────────────────────────────────────────────

    @staticmethod
    def format_date(expense: Expense) -> str:
        raw_date = expense.add_attr.get("date")
        if raw_date:
            try:
                parsed = datetime.fromisoformat(raw_date)
                return parsed.strftime("%Y-%m-%d")
            except Exception:
                return raw_date
        return expense.created_at.strftime("%Y-%m-%d")

    @staticmethod
    @sync_to_async
    def get_expenses_by_chat(chat_id: int):
        filter_condition = Q(chat_id=chat_id) | Q(add_attr__chat_id=chat_id)
        return list(
            Expense.objects.filter(filter_condition)
            .select_related("category", "user")
            .order_by("created_at")
        )

    @staticmethod
    @sync_to_async
    def get_total_by_chat(chat_id: int) -> float:
        filter_condition = Q(chat_id=chat_id) | Q(add_attr__chat_id=chat_id)
        result = Expense.objects.filter(filter_condition).aggregate(
            total=Sum(Abs("amount"))
        )
        return float(result["total"] or 0)

    @staticmethod
    @sync_to_async
    def get_category_summary(chat_id: int):
        filter_condition = Q(chat_id=chat_id) | Q(add_attr__chat_id=chat_id)
        queryset = (
            Expense.objects.filter(filter_condition)
            .values("category__name")
            .annotate(total=Sum(Abs("amount")))
            .order_by("-total")
        )
        return [
            (row["category__name"] or "Без категории", float(row["total"]))
            for row in queryset
        ]

    # ─── Расходы по периоду (user-based, не chat-based) ───────

    @staticmethod
    @sync_to_async
    def get_expenses_by_period(
        user_id: int,
        date_from: date,
        date_to: date,
    ) -> list[Expense]:
        return list(
            Expense.objects.filter(
                user_id=user_id,
                deleted_at__isnull=True,
                created_at__date__gte=date_from,
                created_at__date__lte=date_to,
            )
            .select_related("category")
            .order_by("created_at")
        )

    @staticmethod
    @sync_to_async
    def get_expense_total_by_period(
        user_id: int,
        date_from: date,
        date_to: date,
    ) -> Decimal:
        result = Expense.objects.filter(
            user_id=user_id,
            deleted_at__isnull=True,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        ).aggregate(total=Sum(Abs("amount")))
        return result["total"] or Decimal("0.00")

    @staticmethod
    @sync_to_async
    def get_expense_category_summary_by_period(
        user_id: int,
        date_from: date,
        date_to: date,
    ) -> list[tuple[str, Decimal]]:
        queryset = (
            Expense.objects.filter(
                user_id=user_id,
                deleted_at__isnull=True,
                created_at__date__gte=date_from,
                created_at__date__lte=date_to,
            )
            .values("category__name")
            .annotate(total=Sum(Abs("amount")))
            .order_by("-total")
        )
        return [
            (row["category__name"] or "Без категории", row["total"])
            for row in queryset
        ]

    # ─── Доходы ────────────────────────────────────────────────

    @staticmethod
    @sync_to_async
    def get_income_total_by_period(
        user_id: int,
        date_from: date,
        date_to: date,
    ) -> Decimal:
        result = Income.objects.filter(
            user_id=user_id,
            deleted_at__isnull=True,
            created_at__date__gte=date_from,
            created_at__date__lte=date_to,
        ).aggregate(total=Sum("amount"))
        return result["total"] or Decimal("0.00")

    @staticmethod
    @sync_to_async
    def get_income_category_summary_by_period(
        user_id: int,
        date_from: date,
        date_to: date,
    ) -> list[tuple[str, Decimal]]:
        queryset = (
            Income.objects.filter(
                user_id=user_id,
                deleted_at__isnull=True,
                created_at__date__gte=date_from,
                created_at__date__lte=date_to,
            )
            .values("category__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        return [
            (row["category__name"] or "Без категории", row["total"])
            for row in queryset
        ]

    # ─── Форматирование отчётов ───────────────────────────────

    @staticmethod
    def format_expense_report(
        category_summary: list[tuple[str, Decimal]],
        total: Decimal,
        date_from: date,
        date_to: date,
    ) -> str:
        lines = [
            f"📊 <b>Расходы</b> ({date_from} — {date_to})\n",
        ]
        for idx, (category, amount) in enumerate(category_summary, start=1):
            lines.append(f"{idx}. {category} — {amount:.2f} ₽")

        lines.append(f"\n💸 <b>Итого:</b> {total:.2f} ₽")
        return "\n".join(lines)

    @staticmethod
    def format_income_report(
        category_summary: list[tuple[str, Decimal]],
        total: Decimal,
        date_from: date,
        date_to: date,
    ) -> str:
        lines = [
            f"💰 <b>Доходы</b> ({date_from} — {date_to})\n",
        ]
        for idx, (category, amount) in enumerate(category_summary, start=1):
            lines.append(f"{idx}. {category} — {amount:.2f} ₽")

        lines.append(f"\n💵 <b>Итого:</b> {total:.2f} ₽")
        return "\n".join(lines)

    @staticmethod
    def format_cashflow_report(
        income_total: Decimal,
        expense_total: Decimal,
        date_from: date,
        date_to: date,
    ) -> str:
        net = income_total - expense_total
        net_icon = "📈" if net >= 0 else "📉"
        savings_rate = (
            (net / income_total * 100).quantize(Decimal("0.1"))
            if income_total > 0
            else Decimal("0")
        )

        return (
            f"💹 <b>Cashflow</b> ({date_from} — {date_to})\n\n"
            f"💰 Доходы: {income_total:.2f} ₽\n"
            f"💸 Расходы: {expense_total:.2f} ₽\n"
            f"{net_icon} <b>Итого: {'+' if net >= 0 else ''}{net:.2f} ₽</b>\n"
            f"💾 Норма сбережений: {savings_rate}%"
        )

    @staticmethod
    def format_full_report(
        expense_summary: list[tuple[str, Decimal]],
        expense_total: Decimal,
        income_summary: list[tuple[str, Decimal]],
        income_total: Decimal,
        date_from: date,
        date_to: date,
    ) -> str:
        net = income_total - expense_total
        net_icon = "📈" if net >= 0 else "📉"

        lines = [
            f"📑 <b>Полный отчёт</b> ({date_from} — {date_to})\n",
            "━━━ 💰 Доходы ━━━",
        ]

        if income_summary:
            for idx, (category, amount) in enumerate(income_summary, start=1):
                lines.append(f"  {idx}. {category} — {amount:.2f} ₽")
            lines.append(f"  <b>Итого доходов: {income_total:.2f} ₽</b>")
        else:
            lines.append("  Нет данных")

        lines.append("\n━━━ 💸 Расходы ━━━")

        if expense_summary:
            for idx, (category, amount) in enumerate(expense_summary, start=1):
                lines.append(f"  {idx}. {category} — {amount:.2f} ₽")
            lines.append(f"  <b>Итого расходов: {expense_total:.2f} ₽</b>")
        else:
            lines.append("  Нет данных")

        lines.append(f"\n{net_icon} <b>Баланс: {'+' if net >= 0 else ''}{net:.2f} ₽</b>")

        return "\n".join(lines)
