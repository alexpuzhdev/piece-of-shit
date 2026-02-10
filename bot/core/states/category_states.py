from aiogram.fsm.state import StatesGroup, State


class CategoryRenameStates(StatesGroup):
    """FSM для переименования категории."""
    entering_new_name = State()


class CategoryCreateStates(StatesGroup):
    """FSM для создания новой категории."""
    entering_name = State()
