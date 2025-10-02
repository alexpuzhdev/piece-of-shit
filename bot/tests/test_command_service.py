from datetime import datetime, timedelta

from django.test import SimpleTestCase
from django.utils import timezone

from bot.services.command_service import CommandService


class CommandServicePeriodParsingTests(SimpleTestCase):
    def setUp(self):
        tz = timezone.get_current_timezone()
        self.now = datetime(2023, 5, 20, 12, 0, tzinfo=tz)

    def test_default_period_has_no_label(self):
        period = CommandService.parse_period("/recalculate", now=self.now)
        self.assertIsNone(period.start)
        self.assertIsNone(period.end)
        self.assertEqual(period.label, "")

    def test_parse_period_with_numeric_days(self):
        period = CommandService.parse_period("/recalculate 5", now=self.now)
        expected_start = self.now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=5)
        expected_end = self.now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        self.assertEqual(period.start, expected_start)
        self.assertEqual(period.end, expected_end)
        self.assertEqual(period.label, "за последние 5 дн.")

    def test_parse_period_with_last_days_phrase(self):
        period = CommandService.parse_period("/recalculate последние 7 дней", now=self.now)
        expected_start = self.now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)
        expected_end = self.now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        self.assertEqual(period.start, expected_start)
        self.assertEqual(period.end, expected_end)
        self.assertEqual(period.label, "за последние 7 дн.")
