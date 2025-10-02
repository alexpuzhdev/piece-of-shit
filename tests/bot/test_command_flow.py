from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import types

from bot.core.handlers.expenses import save_expense
from bot.core.handlers.inline import inline_query_handler
from bot.services.command_service import CommandService
from project.apps.core.services import user_start_service
from project.apps.expenses.services import expense_service


@pytest.mark.asyncio
async def test_inline_query_returns_article_for_known_command(monkeypatch):
    bot = AsyncMock()
    query = MagicMock(spec=types.InlineQuery)
    query.query = "help"
    query.answer = AsyncMock()

    await inline_query_handler(query, bot)

    query.answer.assert_awaited()
    answered_results = query.answer.await_args.args[0]
    assert len(answered_results) == 1

    result = answered_results[0]
    assert result.title == CommandService.COMMANDS[0].title
    assert result.input_message_content.message_text == CommandService.COMMANDS[0].message_text


@pytest.mark.asyncio
async def test_expense_handler_delegates_to_command_service_on_mention(monkeypatch):
    bot = AsyncMock()
    bot.get_me = AsyncMock(
        return_value=types.User(id=999, is_bot=True, first_name="Inline", username="test_bot")
    )

    message = MagicMock(spec=types.Message)
    message.text = "@test_bot help"
    message.caption = None
    message.entities = [types.MessageEntity(type="mention", offset=0, length=9)]
    message.caption_entities = None
    message.answer = AsyncMock()
    message.from_user = types.User(id=1, is_bot=False, first_name="User")

    user_service_mock = AsyncMock()
    expense_service_mock = AsyncMock()
    monkeypatch.setattr(user_start_service.UserService, "get_or_create_from_aiogram", user_service_mock)
    monkeypatch.setattr(expense_service.ExpenseService, "create_from_message", expense_service_mock)

    await save_expense(message, bot)

    message.answer.assert_awaited()
    user_service_mock.assert_not_awaited()
    expense_service_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_expense_handler_processes_regular_expense(monkeypatch):
    bot = AsyncMock()
    bot.get_me = AsyncMock()

    message = MagicMock(spec=types.Message)
    message.text = "100 кофе"
    message.caption = None
    message.entities = []
    message.caption_entities = None
    message.answer = AsyncMock()
    message.from_user = types.User(id=2, is_bot=False, first_name="User2")
    message.chat = types.Chat(id=123, type="private")
    message.message_id = 10
    message.date = None

    fake_user = SimpleNamespace(id=1)
    user_service_mock = AsyncMock(return_value=(fake_user, False))
    fake_expense = SimpleNamespace(category=SimpleNamespace(name="Кофе"), amount=100)
    expense_service_mock = AsyncMock(return_value=[fake_expense])

    monkeypatch.setattr(user_start_service.UserService, "get_or_create_from_aiogram", user_service_mock)
    monkeypatch.setattr(expense_service.ExpenseService, "create_from_message", expense_service_mock)

    await save_expense(message, bot)

    user_service_mock.assert_awaited_once()
    expense_service_mock.assert_awaited_once()
    bot.get_me.assert_not_awaited()
    message.answer.assert_not_awaited()
