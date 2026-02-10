from __future__ import annotations

from datetime import date
import re

_MONTHS = {
    "января": 1,
    "янв": 1,
    "февраля": 2,
    "фев": 2,
    "марта": 3,
    "мар": 3,
    "апреля": 4,
    "апр": 4,
    "мая": 5,
    "май": 5,
    "июня": 6,
    "июн": 6,
    "июля": 7,
    "июл": 7,
    "августа": 8,
    "авг": 8,
    "сентября": 9,
    "сент": 9,
    "сен": 9,
    "октября": 10,
    "окт": 10,
    "ноября": 11,
    "ноя": 11,
    "декабря": 12,
    "дек": 12,
}

_NUMERIC_DATE_RE = re.compile(r"^(\d{1,2})[.\-/ ](\d{1,2})(?:[.\-/ ](\d{2,4}))?$")
_WORD_MONTH_RE = re.compile(r"^(\d{1,2})\s+([a-zа-яё\.]+)(?:\s+(\d{4}))?$", re.IGNORECASE)


def parse_user_date(raw_text: str, *, default_year: int | None = None) -> date | None:
    """Парсит дату из пользовательского ввода.

    Поддерживаемые форматы:
    - 13.11
    - 13.11.2026
    - 13-11
    - 13/11
    - 13 ноября
    - 13 ноября 2026
    """
    text = (raw_text or "").strip().lower()
    if not text:
        return None

    numeric_match = _NUMERIC_DATE_RE.match(text)
    if numeric_match:
        day = int(numeric_match.group(1))
        month = int(numeric_match.group(2))
        year_text = numeric_match.group(3)
        year = _resolve_year(year_text, default_year)
        return _safe_date(year, month, day)

    word_match = _WORD_MONTH_RE.match(text)
    if word_match:
        day = int(word_match.group(1))
        month_raw = word_match.group(2).replace(".", "")
        month = _MONTHS.get(month_raw)
        if not month:
            return None
        year_text = word_match.group(3)
        year = _resolve_year(year_text, default_year)
        return _safe_date(year, month, day)

    return None


def _resolve_year(year_text: str | None, default_year: int | None) -> int:
    base_year = default_year or date.today().year
    if not year_text:
        return base_year
    year = int(year_text)
    if year < 100:
        return 2000 + year
    return year


def _safe_date(year: int, month: int, day: int) -> date | None:
    try:
        return date(year, month, day)
    except ValueError:
        return None
