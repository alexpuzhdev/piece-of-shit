from __future__ import annotations

from dataclasses import dataclass
from itertools import chain
from typing import Iterable

from aiogram import Bot, types
from aiogram.types import InlineQueryResultArticle, InputTextMessageContent

from .base_service import BaseService


@dataclass(frozen=True, slots=True)
class CommandDefinition:
    """Description of a bot command that can be invoked without a slash."""

    name: str
    title: str
    description: str
    message_text: str
    parse_mode: str | None = None
    aliases: tuple[str, ...] = ()


class CommandService(BaseService):
    """Utility responsible for recognising and executing bot commands."""

    COMMANDS: tuple[CommandDefinition, ...] = (
        CommandDefinition(
            name="help",
            title="ℹ️ Помощь",
            description="Подсказка по доступным действиям",
            message_text=(
                "ℹ️ Доступные команды:\n"
                "• help — эта справка\n"
                "• recalculate — пересчёт расходов в чате"
            ),
            aliases=("help", "/help", "помощь", "команды"),
        ),
    )

    _alias_map: dict[str, CommandDefinition] = {}

    def __init__(self, bot: Bot):
        super().__init__(bot)

        if not CommandService._alias_map:
            alias_map: dict[str, CommandDefinition] = {}

            for command in self.COMMANDS:
                alias_candidates = set(command.aliases or ()) | {command.name}

                for alias in alias_candidates:
                    normalized = self._normalize_alias(alias)
                    if normalized:
                        alias_map[normalized] = command

            CommandService._alias_map = alias_map

        self._me_cache: types.User | None = None

    @property
    def default_command(self) -> CommandDefinition | None:
        return self.COMMANDS[0] if self.COMMANDS else None

    @staticmethod
    def _normalize_alias(alias: str) -> str:
        return alias.strip().lstrip("/").lower()

    @staticmethod
    def _normalize_token(token: str) -> str:
        return token.strip().lstrip("/").lower()

    @staticmethod
    def _collect_entities(message: types.Message) -> Iterable[types.MessageEntity]:
        return chain(message.entities or (), message.caption_entities or ())

    async def _get_me(self) -> types.User | None:
        if self._me_cache is None:
            try:
                self._me_cache = await self.bot.get_me()
            except Exception:
                self._me_cache = None
        return self._me_cache

    async def _strip_bot_mention(self, text: str) -> str:
        if not text:
            return ""

        stripped = text.strip()
        if not stripped.startswith("@"):
            return stripped

        me = await self._get_me()
        if not me or not me.username:
            return stripped

        username = me.username.lower()

        mention = f"@{username}"
        if stripped.lower().startswith(mention):
            return stripped[len(mention) :].strip()

        return stripped

    def _maybe_has_mention_entity(self, message: types.Message) -> bool:
        for entity in self._collect_entities(message):
            if entity.type in ("mention", "text_mention"):
                return True
        return False

    async def _mentions_bot(self, message: types.Message) -> bool:
        if not self._maybe_has_mention_entity(message):
            return False

        me = await self._get_me()
        if not me:
            return False

        username = (me.username or "").lower()
        text_sources = (message.text or "", message.caption or "")

        for entity in self._collect_entities(message):
            if entity.type == "text_mention" and entity.user and entity.user.id == me.id:
                return True

            if entity.type == "mention" and username:
                for source in text_sources:
                    if not source:
                        continue
                    start = entity.offset
                    end = entity.offset + entity.length
                    mention_text = source[start:end]
                    if mention_text.lower() == f"@{username}":
                        return True

        return False

    def get_command_from_text(self, text: str) -> CommandDefinition | None:
        if not text:
            return None

        stripped = text.strip()
        if not stripped:
            return None

        token = stripped.split()[0]
        normalized = self._normalize_token(token)
        if not normalized:
            return None

        return self._alias_map.get(normalized)

    async def get_command_from_message(self, message: types.Message) -> CommandDefinition | None:
        text = message.text or message.caption or ""
        text = await self._strip_bot_mention(text)
        return self.get_command_from_text(text)

    async def handle_message(self, message: types.Message) -> bool:
        command = await self.get_command_from_message(message)
        mentions_bot = await self._mentions_bot(message)

        if not command and not mentions_bot:
            return False

        command_to_execute = command or self.default_command
        if not command_to_execute:
            return False

        await message.answer(
            command_to_execute.message_text,
            parse_mode=command_to_execute.parse_mode,
        )

        return True

    def build_inline_article(self, command: CommandDefinition) -> InlineQueryResultArticle:
        return InlineQueryResultArticle(
            id=command.name,
            title=command.title,
            description=command.description,
            input_message_content=InputTextMessageContent(
                message_text=command.message_text,
                parse_mode=command.parse_mode,
            ),
        )

    async def handle_inline_query(self, inline_query: types.InlineQuery) -> list[InlineQueryResultArticle]:
        command = self.get_command_from_text(inline_query.query or "")
        if not command:
            return []

        return [self.build_inline_article(command)]

    async def on_chosen_inline_result(self, result: types.ChosenInlineResult) -> None:
        # For now we only keep the hook for future extensions (logging, metrics, etc.)
        return None
