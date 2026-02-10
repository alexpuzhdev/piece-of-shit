from aiogram import Router, types, Bot, F
from aiogram.fsm.context import FSMContext

from bot.core.callbacks.menu import MenuAction, MENU_FEEDBACK
from bot.core.keyboards.menu import main_menu_keyboard
from bot.core.states.feedback_states import FeedbackStates
from bot.core.texts import t
from bot.services.fsm_message_tracker import edit_and_track, send_and_track, cleanup_tracked, set_fsm_return_to
from bot.services.message_service import MessageService
from project.apps.core.services.user_start_service import UserService
from project.apps.core.models import Feedback


feedback_router = Router()


@feedback_router.callback_query(MenuAction.filter(F.action == MENU_FEEDBACK))
async def feedback_start(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    await state.set_state(FeedbackStates.entering_message)
    await set_fsm_return_to(state, "back")
    await edit_and_track(callback.message, state, t("feedback.prompt"))
    await callback.answer()


@feedback_router.message(FeedbackStates.entering_message)
async def feedback_save(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)

    text = (message.text or "").strip()
    if not text:
        await send_and_track(bot, message.chat.id, state, t("error.empty_feedback"))
        return

    user, _ = await UserService.get_or_create_from_aiogram(message.from_user)
    await Feedback.objects.acreate(user=user, text=text, chat_id=message.chat.id)

    await cleanup_tracked(bot, state)
    await state.clear()

    await bot.send_message(message.chat.id, t("feedback.thanks"), reply_markup=main_menu_keyboard())
