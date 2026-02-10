from aiogram.fsm.state import State, StatesGroup


class GoalStates(StatesGroup):
    """Состояния FSM для создания и пополнения целей."""
    entering_name = State()
    entering_target_amount = State()
    entering_deadline = State()
    entering_deposit_amount = State()
    entering_total_savings = State()
    selecting_goals_savings = State()
