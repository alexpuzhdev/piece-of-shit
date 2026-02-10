from aiogram.fsm.state import State, StatesGroup


class ReportStates(StatesGroup):
    """Состояния FSM для выбора периода отчёта через календарь."""
    choosing_report_type = State()
    choosing_start_date = State()
    choosing_end_date = State()
