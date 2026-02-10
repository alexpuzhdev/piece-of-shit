"""Реестр текстов бота.

Стратегия:
1. При старте бота вызывается load() — загружаются тексты из БД в память.
2. get(key) сначала ищет в кеше (БД), затем в defaults.
3. Если ключ не найден нигде — возвращается placeholder [key].
4. Поддерживает .format(**kwargs) для подстановки параметров.
"""

import logging

from bot.core.texts.defaults import DEFAULTS

logger = logging.getLogger(__name__)


class BotTextRegistry:
    """Реестр текстов с кешированием записей из БД."""

    _cache: dict[str, str] | None = None

    @classmethod
    async def load(cls) -> None:
        """Загружает все тексты из БД в память.
        Вызывается один раз при старте бота."""
        from project.apps.core.models import BotText

        texts = {}
        async for bot_text in BotText.objects.filter(deleted_at__isnull=True):
            texts[bot_text.key] = bot_text.value

        cls._cache = texts
        logger.info(
            "BotTextRegistry: загружено %d текстов из БД, %d дефолтов",
            len(texts),
            len(DEFAULTS),
        )

    @classmethod
    async def reload(cls) -> None:
        """Перезагружает кеш из БД."""
        await cls.load()

    @classmethod
    def get(cls, key: str, **kwargs) -> str:
        """Возвращает текст по ключу.

        Приоритет: БД (кеш) → defaults → placeholder.
        kwargs подставляются через str.format()."""
        # 1. Из БД (кеш)
        if cls._cache and key in cls._cache:
            text = cls._cache[key]
        # 2. Из дефолтов
        elif key in DEFAULTS:
            text = DEFAULTS[key]
        # 3. Placeholder — сразу видно, что текст не найден
        else:
            logger.warning("BotTextRegistry: ключ '%s' не найден", key)
            return f"[{key}]"

        if kwargs:
            try:
                return text.format(**kwargs)
            except (KeyError, IndexError):
                logger.warning(
                    "BotTextRegistry: ошибка форматирования '%s' с %s",
                    key,
                    kwargs,
                )
                return text

        return text
