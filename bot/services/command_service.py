from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Optional

from django.utils import timezone

from project.apps.expenses.services.periods import PeriodRange


class CommandService:
    """Utilities to help parsing bot commands."""

    _DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")

    @classmethod
    def parse_period(cls, text: str, now: Optional[datetime] = None) -> PeriodRange:
        """Extract a period range from command text."""

        query = cls._extract_query(text)
        if not query:
            return PeriodRange()

        normalized = " ".join(query.lower().split())
        normalized = normalized.replace("за ", "").strip()

        now = (now or timezone.now()).astimezone(timezone.get_current_timezone())

        if not normalized or normalized in {"all", "всё", "все", "за всё время", "все время"}:
            return PeriodRange()

        if any(key in normalized for key in ("today", "сегодня")):
            start = cls._start_of_day(now)
            return PeriodRange(start=start, end=start + timedelta(days=1), label="за сегодня")

        if any(key in normalized for key in ("yesterday", "вчера")):
            start = cls._start_of_day(now - timedelta(days=1))
            return PeriodRange(start=start, end=start + timedelta(days=1), label="за вчера")

        if "прошл" in normalized and cls._contains_week(normalized):
            end = cls._start_of_week(now)
            start = end - timedelta(days=7)
            return PeriodRange(start=start, end=end, label="за прошлую неделю")

        if cls._contains_week(normalized):
            start = cls._start_of_week(now)
            return PeriodRange(start=start, end=start + timedelta(days=7), label="за эту неделю")

        if "прошл" in normalized and cls._contains_month(normalized):
            start, end = cls._previous_month(now)
            return PeriodRange(start=start, end=end, label="за прошлый месяц")

        if cls._contains_month(normalized):
            start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end = cls._next_month(start)
            return PeriodRange(start=start, end=end, label="за этот месяц")

        if "прошл" in normalized and cls._contains_year(normalized):
            start = now.replace(year=now.year - 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=start.year + 1)
            return PeriodRange(start=start, end=end, label="за прошлый год")

        if cls._contains_year(normalized):
            start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end = start.replace(year=start.year + 1)
            return PeriodRange(start=start, end=end, label="за этот год")

        date_matches = cls._DATE_PATTERN.findall(normalized)
        if date_matches:
            return cls._period_from_dates(date_matches)

        if normalized.isdigit():
            days = int(normalized)
            start = cls._start_of_day(now - timedelta(days=days))
            return PeriodRange(
                start=start,
                end=cls._start_of_day(now) + timedelta(days=1),
                label=f"за последние {days} дн.",
            )

        return PeriodRange(label=query)

    @staticmethod
    def _extract_query(text: str) -> str:
        if not text:
            return ""
        text = text.strip()
        if not text:
            return ""
        if text.startswith("/"):
            parts = text.split(maxsplit=1)
            if len(parts) == 1:
                return ""
            return parts[1]
        return text

    @staticmethod
    def _start_of_day(dt: datetime) -> datetime:
        return dt.replace(hour=0, minute=0, second=0, microsecond=0)

    @staticmethod
    def _start_of_week(dt: datetime) -> datetime:
        weekday = dt.weekday()
        return CommandService._start_of_day(dt - timedelta(days=weekday))

    @staticmethod
    def _contains_week(text: str) -> bool:
        return "week" in text or "недел" in text

    @staticmethod
    def _contains_month(text: str) -> bool:
        return "month" in text or "месяц" in text

    @staticmethod
    def _contains_year(text: str) -> bool:
        return "year" in text or "год" in text

    @staticmethod
    def _next_month(start: datetime) -> datetime:
        year = start.year + (start.month // 12)
        month = 1 if start.month == 12 else start.month + 1
        if start.month == 12:
            year = start.year + 1
        return start.replace(year=year, month=month, day=1)

    @staticmethod
    def _previous_month(now: datetime) -> tuple[datetime, datetime]:
        if now.month == 1:
            start = now.replace(year=now.year - 1, month=12, day=1, hour=0, minute=0, second=0, microsecond=0)
        else:
            start = now.replace(month=now.month - 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        end = CommandService._next_month(start)
        return start, end

    @classmethod
    def _period_from_dates(cls, matches: list[str]) -> PeriodRange:
        tz = timezone.get_current_timezone()

        def _to_date(value: str) -> datetime:
            parsed = datetime.fromisoformat(value)
            parsed = parsed.replace(tzinfo=tz)
            return parsed

        dates = [_to_date(value) for value in matches[:2]]
        dates.sort()
        start = cls._start_of_day(dates[0])
        end = start + timedelta(days=1)
        label = f"за {start.date().isoformat()}"
        if len(dates) == 2:
            end = cls._start_of_day(dates[1]) + timedelta(days=1)
            label = f"с {start.date().isoformat()} по {(end - timedelta(days=1)).date().isoformat()}"
        return PeriodRange(start=start, end=end, label=label)
