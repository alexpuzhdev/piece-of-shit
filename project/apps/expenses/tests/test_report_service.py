from decimal import Decimal
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from project.apps.expenses.models import Category, Expense
from project.apps.expenses.services.periods import PeriodRange
from project.apps.expenses.services.report_service import ReportService


class ReportServicePeriodFilteringTests(TestCase):
    def setUp(self):
        self.now = timezone.now().replace(microsecond=0)
        self.chat_id = 5001
        self.user = get_user_model().objects.create_user(
            username="tester",
            password="pass",
            tg_id=123456,
        )
        self.category_food = Category.objects.create(name="Тестовая еда")
        self.category_travel = Category.objects.create(name="Тестовые поездки")

        self._create_expense(
            amount=Decimal("100.00"),
            category=self.category_food,
            created_at=self.now - timedelta(days=5),
        )
        self._create_expense(
            amount=Decimal("200.00"),
            category=self.category_food,
            created_at=self.now - timedelta(days=2),
        )
        self._create_expense(
            amount=Decimal("300.00"),
            category=self.category_travel,
            created_at=self.now - timedelta(days=1),
            chat_id=None,
            add_attr={"chat_id": self.chat_id},
        )
        # Expense in another chat to ensure filtering works.
        self._create_expense(
            amount=Decimal("400.00"),
            category=self.category_travel,
            created_at=self.now - timedelta(days=1),
            chat_id=self.chat_id + 1,
        )

    def _create_expense(self, amount, category, created_at, chat_id=None, add_attr=None):
        expense = Expense.objects.create(
            user=self.user,
            amount=amount,
            chat_id=self.chat_id if chat_id is None else chat_id,
            category=category,
            add_attr=add_attr or {},
        )
        Expense.objects.filter(pk=expense.pk).update(created_at=created_at)
        expense.refresh_from_db()
        return expense

    def test_calculate_total_filters_by_period(self):
        period = PeriodRange(
            start=self.now - timedelta(days=3),
            end=self.now + timedelta(days=1),
        )
        total = ReportService.calculate_total(
            self.chat_id,
            start=period.start,
            end=period.end,
        )
        self.assertEqual(total, 500.0)

    def test_category_summary_uses_period_and_chat(self):
        period = PeriodRange(
            start=self.now - timedelta(days=3),
            end=self.now + timedelta(days=1),
        )
        summary = ReportService.calculate_category_summary(
            self.chat_id,
            start=period.start,
            end=period.end,
        )
        self.assertEqual(summary, [(self.category_travel.name, 300.0), (self.category_food.name, 200.0)])

    def test_calculate_dynamics_generates_previous_period(self):
        period = PeriodRange(
            start=self.now - timedelta(days=3),
            end=self.now,
        )
        dynamics = ReportService.calculate_dynamics(self.chat_id, current_period=period)
        self.assertEqual(dynamics["current"], 500.0)
        self.assertEqual(dynamics["previous"], 100.0)
        self.assertEqual(dynamics["difference"], 400.0)
