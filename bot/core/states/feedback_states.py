from aiogram.fsm.state import StatesGroup, State


class FeedbackStates(StatesGroup):
    """FSM для обратной связи."""
    entering_message = State()
