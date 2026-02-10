from aiogram.fsm.state import StatesGroup, State


class QuickEntryStates(StatesGroup):
    """FSM-состояния быстрого ввода: сумма → тип → категория."""
    entering_amount = State()
    choosing_type = State()
    choosing_category = State()
