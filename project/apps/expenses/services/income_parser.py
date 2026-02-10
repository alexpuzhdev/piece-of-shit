import re
from decimal import Decimal, InvalidOperation
from typing import List, Tuple


class IncomeParser:
    """Определяет, является ли сообщение записью дохода, и парсит сумму + категорию.

    Сообщение трактуется как доход, если:
    - начинается с «+» перед числом (например: +50000 зарплата);
    - содержит ключевое слово-маркер дохода (доход, зарплата, аванс, приход и т.д.).
    """

    INCOME_KEYWORDS = (
        "доход",
        "зарплата",
        "аванс",
        "приход",
        "получил",
        "получила",
        "заработал",
        "заработала",
        "перевод",
        "премия",
        "гонорар",
        "возврат",
        "кэшбэк",
        "кешбэк",
        "cashback",
    )

    # Регулярка для «+сумма» в начале строки
    PLUS_AMOUNT_RE = re.compile(
        r"""
        ^\s*\+\s*
        (?P<num>\d[\d\s.,]*)
        \s*
        (?P<cur>(?:₽|руб(?:\.|лей)?|r|rub)?)
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    # Универсальная регулярка для суммы (без обязательного +)
    AMOUNT_RE = re.compile(
        r"""
        (?P<num>\d[\d\s.,]*)
        \s*
        (?P<cur>(?:₽|руб(?:\.|лей)?|r|rub)?)
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    @classmethod
    def is_income_message(cls, text: str) -> bool:
        """Определяет, содержит ли сообщение маркеры дохода."""
        if not text:
            return False

        stripped = text.strip()

        # Явный плюс перед числом
        if cls.PLUS_AMOUNT_RE.search(stripped):
            return True

        lowered = stripped.lower()
        return any(keyword in lowered for keyword in cls.INCOME_KEYWORDS)

    @classmethod
    def _normalize_number(cls, raw: str) -> Decimal | None:
        """Нормализация числовой строки в Decimal.
        Логика идентична ExpenseParser для единообразия."""
        cleaned = raw.replace("\xa0", " ").strip().replace(" ", "")

        if "." in cleaned and "," in cleaned:
            last_dot = cleaned.rfind(".")
            last_comma = cleaned.rfind(",")
            decimal_sep = "." if last_dot > last_comma else ","
            tail = cleaned.split(decimal_sep)[-1]
            if 1 <= len(tail) <= 2:
                sep = decimal_sep
            else:
                sep = None
        elif "." in cleaned:
            tail = cleaned.split(".")[-1]
            sep = "." if 1 <= len(tail) <= 2 else None
        elif "," in cleaned:
            tail = cleaned.split(",")[-1]
            sep = "," if 1 <= len(tail) <= 2 else None
        else:
            sep = None

        if sep:
            other = "," if sep == "." else "."
            cleaned = cleaned.replace(other, "").replace(sep, ".")
        else:
            cleaned = cleaned.replace(".", "").replace(",", "")

        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None

    @classmethod
    def _strip_match_from_line(cls, line: str, match: re.Match) -> str:
        start, end = match.span()
        return (line[:start] + line[end:]).strip()

    @classmethod
    def _remove_income_keywords(cls, text: str) -> str:
        """Убирает ключевые слова-маркеры дохода из строки описания."""
        result = text
        for keyword in cls.INCOME_KEYWORDS:
            result = re.sub(
                rf"\b{re.escape(keyword)}\b",
                "",
                result,
                flags=re.IGNORECASE,
            )
        return result.strip()

    @classmethod
    def parse(cls, text: str) -> List[Tuple[Decimal, str]]:
        """Парсит текст и возвращает список (сумма, описание/категория).
        Возвращает пустой список, если сообщение не является доходом."""
        if not cls.is_income_message(text):
            return []

        lines = [line.strip() for line in (text or "").splitlines()]
        lines = [line for line in lines if line]

        results: List[Tuple[Decimal, str]] = []

        for line in lines:
            # Пробуем формат «+сумма описание»
            match = cls.PLUS_AMOUNT_RE.search(line)
            if match:
                raw_num = match.group("num").strip()
                amount = cls._normalize_number(raw_num)
                if amount is None:
                    continue
                description = cls._strip_match_from_line(line, match)
                description = cls._remove_income_keywords(description)
                if not description:
                    description = "Без описания"
                results.append((abs(amount), description))
                continue

            # Пробуем формат «ключевое_слово сумма описание»
            match = cls.AMOUNT_RE.search(line)
            if match:
                raw_num = match.group("num").strip()
                amount = cls._normalize_number(raw_num)
                if amount is None:
                    continue
                description = cls._strip_match_from_line(line, match)
                description = cls._remove_income_keywords(description)
                if not description:
                    description = "Без описания"
                results.append((abs(amount), description))

        return results
