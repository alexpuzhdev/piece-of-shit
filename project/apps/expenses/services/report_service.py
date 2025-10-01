from asgiref.sync import sync_to_async
from project.apps.expenses.models import Expense
from django.db.models import Sum
from datetime import datetime


class ReportService:
    @staticmethod
    def format_date(expense: Expense) -> str:
        raw_date = expense.add_attr.get("date")
        if raw_date:
            try:
                dt = datetime.fromisoformat(raw_date)
                return dt.strftime("%Y-%m-%d")
            except Exception:
                return raw_date  # fallback если вдруг строка битая
        return expense.created_at.strftime("%Y-%m-%d")

    @staticmethod
    @sync_to_async
    def get_expenses_by_chat(chat_id: int):
        return list(
            Expense.objects.filter(add_attr__chat_id=chat_id)
            .select_related("category", "user")
            .order_by("created_at")
        )

    @staticmethod
    @sync_to_async
    def get_total_by_chat(chat_id: int) -> float:
        result = (
            Expense.objects.filter(add_attr__chat_id=chat_id)
            .aggregate(total=Sum("amount"))
        )
        return float(result["total"] or 0)

    @staticmethod
    @sync_to_async
    def get_category_summary(chat_id: int):
        qs = (
            Expense.objects.filter(add_attr__chat_id=chat_id)
            .values("category__name")
            .annotate(total=Sum("amount"))
            .order_by("-total")
        )
        return {row["category__name"] or "Без категории": float(row["total"]) for row in qs}
