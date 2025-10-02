from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class PeriodRange:
    """Represents a time range for expense reports."""

    start: Optional[datetime] = None
    end: Optional[datetime] = None
    label: str = "за всё время"

    def duration(self):
        if self.start and self.end:
            return self.end - self.start
        return None

    def with_label(self, label: str) -> "PeriodRange":
        return PeriodRange(start=self.start, end=self.end, label=label)
