from aiogram.fsm.state import State, StatesGroup


class PlannedStates(StatesGroup):
    """Состояния FSM для создания плановых трат."""
    entering_description = State()
    entering_amount = State()
    entering_date = State()
    entering_category = State()
