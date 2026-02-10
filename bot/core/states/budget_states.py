from aiogram.fsm.state import State, StatesGroup


class BudgetStates(StatesGroup):
    """Состояния FSM для настройки бюджета."""
    entering_general_limit = State()
    entering_category_limit = State()
    choosing_category = State()
