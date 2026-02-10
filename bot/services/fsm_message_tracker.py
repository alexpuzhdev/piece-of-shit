"""Утилита для отслеживания и удаления промежуточных сообщений бота
в FSM-потоках. Решает проблему «засирания» чата.

Также добавляет кнопку «Отмена» к каждому промежуточному сообщению,
чтобы пользователь мог выйти из FSM-потока в любой момент.
"""

import asyncio

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext

from bot.core.callbacks.menu import FsmCancelAction

_TRACKED_KEY = "_tracked_bot_msg_id"
_TRACKED_CHAT_KEY = "_tracked_chat_id"
_RETURN_TO_KEY = "_fsm_return_to"


def _cancel_keyboard(return_to: str) -> types.InlineKeyboardMarkup:
    """Клавиатура с единственной кнопкой «Отмена»."""
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text="❌ Отмена",
                callback_data=FsmCancelAction(return_to=return_to).pack(),
            ),
        ],
    ])


def _merge_cancel_button(
    reply_markup: types.InlineKeyboardMarkup | None,
    return_to: str,
) -> types.InlineKeyboardMarkup:
    """Добавляет кнопку «Отмена» к существующей клавиатуре или создаёт новую."""
    cancel_row = [
        types.InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=FsmCancelAction(return_to=return_to).pack(),
        ),
    ]

    if reply_markup:
        rows = list(reply_markup.inline_keyboard) + [cancel_row]
        return types.InlineKeyboardMarkup(inline_keyboard=rows)

    return types.InlineKeyboardMarkup(inline_keyboard=[cancel_row])


async def send_and_track(
    bot: Bot,
    chat_id: int,
    state: FSMContext,
    text: str,
    reply_markup: types.InlineKeyboardMarkup | None = None,
    parse_mode: str | None = "HTML",
) -> types.Message:
    """Отправляет сообщение и запоминает его ID в FSM-данных.
    Предыдущее отслеживаемое сообщение удаляется автоматически.
    К сообщению добавляется кнопка «Отмена»."""
    await _delete_tracked(bot, state)

    # Добавляем кнопку отмены
    data = await state.get_data()
    return_to = data.get(_RETURN_TO_KEY, "back")
    keyboard = _merge_cancel_button(reply_markup, return_to)

    new_message = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=keyboard,
        parse_mode=parse_mode,
    )

    await state.update_data(
        **{
            _TRACKED_KEY: new_message.message_id,
            _TRACKED_CHAT_KEY: chat_id,
        }
    )
    return new_message


async def edit_and_track(
    message: types.Message,
    state: FSMContext,
    text: str,
    reply_markup: types.InlineKeyboardMarkup | None = None,
) -> types.Message:
    """Редактирует существующее сообщение (callback) и запоминает его."""
    data = await state.get_data()
    return_to = data.get(_RETURN_TO_KEY, "back")
    keyboard = _merge_cancel_button(reply_markup, return_to)

    result = await message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")

    await state.update_data(
        **{
            _TRACKED_KEY: message.message_id,
            _TRACKED_CHAT_KEY: message.chat.id,
        }
    )
    return result


async def set_fsm_return_to(state: FSMContext, return_to_callback: str) -> None:
    """Устанавливает callback для кнопки «Отмена» в текущем FSM-потоке."""
    await state.update_data(**{_RETURN_TO_KEY: return_to_callback})


async def cleanup_tracked(bot: Bot, state: FSMContext) -> None:
    """Удаляет последнее отслеживаемое сообщение."""
    await _delete_tracked(bot, state)


async def send_temporary(
    bot: Bot,
    chat_id: int,
    text: str,
    reply_markup: types.InlineKeyboardMarkup | None = None,
    delay_seconds: int = 5,
) -> None:
    """Отправляет временное сообщение, которое удалится через delay_seconds."""
    msg = await bot.send_message(
        chat_id=chat_id,
        text=text,
        reply_markup=reply_markup,
        parse_mode="HTML",
    )
    asyncio.create_task(_delayed_delete(bot, chat_id, msg.message_id, delay_seconds))


async def _delete_tracked(bot: Bot, state: FSMContext) -> None:
    data = await state.get_data()
    msg_id = data.get(_TRACKED_KEY)
    chat_id = data.get(_TRACKED_CHAT_KEY)

    if msg_id and chat_id:
        try:
            await bot.delete_message(chat_id=chat_id, message_id=msg_id)
        except Exception:
            pass

        await state.update_data(**{_TRACKED_KEY: None, _TRACKED_CHAT_KEY: None})


async def _delayed_delete(bot: Bot, chat_id: int, message_id: int, delay: int) -> None:
    await asyncio.sleep(delay)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
    except Exception:
        pass
