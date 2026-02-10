import calendar
from datetime import date

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.core.callbacks.calendar import (
    CalendarAction,
    CAL_PREV_MONTH,
    CAL_NEXT_MONTH,
    CAL_SELECT_DAY,
    CAL_IGNORE,
)
from bot.core.callbacks.menu import MenuAction, MENU_BACK

WEEKDAY_LABELS = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
MONTH_NAMES_RU = [
    "",
    "Январь", "Февраль", "Март", "Апрель",
    "Май", "Июнь", "Июль", "Август",
    "Сентябрь", "Октябрь", "Ноябрь", "Декабрь",
]


def build_calendar_keyboard(
    year: int | None = None,
    month: int | None = None,
) -> InlineKeyboardMarkup:
    """Строит inline-клавиатуру календаря для выбора даты.

    Показывает один месяц с возможностью навигации ←/→.
    Каждый день — кнопка с callback CalendarAction(action='day', year, month, day).
    """
    today = date.today()
    target_year = year or today.year
    target_month = month or today.month

    rows: list[list[InlineKeyboardButton]] = []

    # ─── Заголовок: ◀ Месяц Год ▶ ─────────────────────
    header_text = f"{MONTH_NAMES_RU[target_month]} {target_year}"

    prev_month = target_month - 1
    prev_year = target_year
    if prev_month < 1:
        prev_month = 12
        prev_year -= 1

    next_month = target_month + 1
    next_year = target_year
    if next_month > 12:
        next_month = 1
        next_year += 1

    rows.append([
        InlineKeyboardButton(
            text="◀",
            callback_data=CalendarAction(
                action=CAL_PREV_MONTH,
                year=prev_year,
                month=prev_month,
            ).pack(),
        ),
        InlineKeyboardButton(
            text=header_text,
            callback_data=CalendarAction(action=CAL_IGNORE).pack(),
        ),
        InlineKeyboardButton(
            text="▶",
            callback_data=CalendarAction(
                action=CAL_NEXT_MONTH,
                year=next_year,
                month=next_month,
            ).pack(),
        ),
    ])

    # ─── Дни недели ────────────────────────────────────
    rows.append([
        InlineKeyboardButton(
            text=day_label,
            callback_data=CalendarAction(action=CAL_IGNORE).pack(),
        )
        for day_label in WEEKDAY_LABELS
    ])

    # ─── Сетка дней ────────────────────────────────────
    month_calendar = calendar.monthcalendar(target_year, target_month)

    for week in month_calendar:
        week_row = []
        for day_number in week:
            if day_number == 0:
                week_row.append(
                    InlineKeyboardButton(
                        text=" ",
                        callback_data=CalendarAction(action=CAL_IGNORE).pack(),
                    )
                )
            else:
                # Отмечаем сегодняшний день
                label = str(day_number)
                if (
                    target_year == today.year
                    and target_month == today.month
                    and day_number == today.day
                ):
                    label = f"•{day_number}•"

                week_row.append(
                    InlineKeyboardButton(
                        text=label,
                        callback_data=CalendarAction(
                            action=CAL_SELECT_DAY,
                            year=target_year,
                            month=target_month,
                            day=day_number,
                        ).pack(),
                    )
                )
        rows.append(week_row)

    # ─── Кнопка «Отмена» ──────────────────────────────
    rows.append([
        InlineKeyboardButton(
            text="❌ Отмена",
            callback_data=MenuAction(action=MENU_BACK).pack(),
        ),
    ])

    return InlineKeyboardMarkup(inline_keyboard=rows)
