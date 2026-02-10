from aiogram.filters.callback_data import CallbackData


class CalendarAction(CallbackData, prefix="cal"):
    """Callback data для inline-календаря."""
    action: str
    year: int = 0
    month: int = 0
    day: int = 0


# Действия календаря
CAL_PREV_MONTH = "prev"
CAL_NEXT_MONTH = "next"
CAL_SELECT_DAY = "day"
CAL_IGNORE = "ignore"
