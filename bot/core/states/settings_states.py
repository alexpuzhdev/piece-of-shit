from aiogram.fsm.state import State, StatesGroup


class ScheduleStates(StatesGroup):
    """Состояния FSM для настройки расписаний доходов."""
    entering_name = State()
    entering_day = State()
    entering_amount = State()


class VacationStates(StatesGroup):
    """Состояния FSM для добавления периода отпуска."""
    entering_start_date = State()
    entering_end_date = State()
    entering_multiplier = State()


class FamilyCreateStates(StatesGroup):
    """Состояния FSM для создания семейной группы."""
    entering_name = State()


class FamilyJoinStates(StatesGroup):
    """Состояния FSM для присоединения к группе по коду."""
    entering_code = State()
