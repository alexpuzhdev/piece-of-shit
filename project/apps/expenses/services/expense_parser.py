import re
from decimal import Decimal, InvalidOperation
from typing import List, Tuple


class ExpenseParser:

    AMOUNT_RE = re.compile(
        r"""
        (?P<sign>[+-]?)
        \s*
        (?P<num>\d[\d\s.,]*)
        \s*
        (?P<cur>(?:₽|руб(?:\.|лей)?|r|rub)?)
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    @classmethod
    def _normalize_number(cls, raw: str) -> Decimal | None:
        s = raw.replace("\xa0", " ").strip()
        s = s.replace(" ", "")

        if "." in s and "," in s:
            last_dot = s.rfind(".")
            last_com = s.rfind(",")
            cand = "." if last_dot > last_com else ","
            tail = s.split(cand)[-1]
            if 1 <= len(tail) <= 2:
                dec = cand
            else:
                dec = None
        else:
            if "." in s:
                tail = s.split(".")[-1]
                dec = "." if 1 <= len(tail) <= 2 else None
            elif "," in s:
                tail = s.split(",")[-1]
                dec = "," if 1 <= len(tail) <= 2 else None
            else:
                dec = None

        if dec:
            other = "," if dec == "." else "."
            s = s.replace(other, "")
            s = s.replace(dec, ".")
        else:
            s = s.replace(".", "").replace(",", "")

        try:
            return Decimal(s)
        except InvalidOperation:
            return None

    @classmethod
    def _strip_match_from_line(cls, line: str, match: re.Match) -> str:
        start, end = match.span()
        return (line[:start] + line[end:]).strip()

    @classmethod
    def parse(cls, text: str) -> List[Tuple[Decimal, str]]:
        lines = [ln.strip() for ln in (text or "").splitlines()]
        lines = [ln for ln in lines if ln]

        results: List[Tuple[Decimal, str]] = []

        def has_amount(s: str) -> bool:
            return bool(cls.AMOUNT_RE.search(s or ""))

        i = 0
        while i < len(lines):
            line = lines[i]
            m = cls.AMOUNT_RE.search(line)
            if not m:
                i += 1
                continue

            sign = (m.group("sign") or "").strip()
            raw_num = (m.group("num") or "").strip()

            amount = cls._normalize_number(raw_num)
            if amount is None:
                i += 1
                continue
            if sign == "-":
                amount = abs(amount)

            category = cls._strip_match_from_line(line, m)

            if not category:
                prev = lines[i - 1] if i - 1 >= 0 else ""
                if prev and not has_amount(prev):
                    category = prev.strip()
                else:
                    nxt = lines[i + 1] if i + 1 < len(lines) else ""
                    if nxt and not has_amount(nxt):
                        category = nxt.strip()

            if not category:
                category = "Без категории"

            results.append((amount, category))
            i += 1

        return results
