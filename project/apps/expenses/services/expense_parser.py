import re
from decimal import Decimal


class ExpenseParser:
    AMOUNT_PATTERN = re.compile(r"(-?\d[\d\s.,]*)\s*[₽рR]?", re.IGNORECASE)

    @classmethod
    def parse(cls, text: str) -> tuple[Decimal | None, str]:
        match = cls.AMOUNT_PATTERN.search(text)
        if not match:
            return None, text.strip()

        raw_amount = match.group(1)

        normalized = raw_amount.replace(" ", "").replace("\xa0", "")

        if normalized.count(".") > 1:
            normalized = normalized.replace(".", "", normalized.count(".") - 1)

        normalized = normalized.replace(",", ".")

        try:
            amount = Decimal(normalized)
        except Exception:
            return None, text.strip()

        description = text.replace(match.group(0), "").strip()
        return amount, description or "Без категории"
