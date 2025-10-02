from __future__ import annotations

import re

__all__ = [
    "normalize_command_text",
]


_whitespace_re = re.compile(r"\s+")
_mention_re = re.compile(r"@[^\s]+$")


def normalize_command_text(text: str | None) -> str:
    """Normalize a command trigger for lookup.

    The normalization is intentionally simple: we lower the text, strip surrounding
    whitespace, drop a leading slash and optional bot mention, collapse repeated
    spaces and replace the ``ё`` letter with ``е`` for resilient matching.
    """

    if not text:
        return ""

    normalized = text.strip().lower()
    normalized = normalized.replace("ё", "е")
    normalized = normalized.lstrip("/")
    # Telegram appends bot mention to slash commands like `/cmd@bot` – remove it.
    normalized = _mention_re.sub("", normalized)
    normalized = normalized.replace("\n", " ")
    normalized = _whitespace_re.sub(" ", normalized)
    return normalized.strip()
