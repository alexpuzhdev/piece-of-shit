from datetime import date
from decimal import Decimal, InvalidOperation

from aiogram import Router, types, Bot, F
from aiogram.fsm.context import FSMContext
from asgiref.sync import sync_to_async

from bot.core.callbacks.calendar import (
    CalendarAction, CAL_PREV_MONTH, CAL_NEXT_MONTH, CAL_SELECT_DAY, CAL_IGNORE,
)
from bot.core.callbacks.menu import (
    SettingsAction, MenuAction,
    SETTINGS_INCOME_SCHEDULE, SETTINGS_VACATION,
    SETTINGS_ADD_SCHEDULE, SETTINGS_ADD_VACATION,
    SETTINGS_FAMILY, SETTINGS_CREATE_FAMILY, SETTINGS_JOIN_FAMILY,
    SETTINGS_LEAVE_FAMILY, MENU_SETTINGS,
)
from bot.core.keyboards.calendar import build_calendar_keyboard
from bot.core.keyboards.menu import back_to_parent_keyboard, settings_menu_keyboard
from bot.core.states.settings_states import (
    ScheduleStates, VacationStates, FamilyCreateStates, FamilyJoinStates,
)
from bot.core.texts import t
from bot.services.fsm_message_tracker import (
    send_and_track, edit_and_track, cleanup_tracked, send_temporary, set_fsm_return_to,
)
from bot.services.message_service import MessageService
from bot.services.date_parser import parse_user_date
from project.apps.core.services.user_start_service import UserService
from project.apps.core.services.family_group_service import FamilyGroupService
from project.apps.expenses.models import IncomeSchedule, VacationPeriod

settings_router = Router()
_BACK_TO_SETTINGS = MenuAction(action=MENU_SETTINGS).pack()


async def _get_user(event):
    user, _ = await UserService.get_or_create_from_aiogram(event.from_user)
    return user


# ═══════════════════════════════════════════════════════════
# Расписания доходов
# ═══════════════════════════════════════════════════════════

@settings_router.callback_query(SettingsAction.filter(F.action == SETTINGS_INCOME_SCHEDULE))
async def income_schedule_list(callback: types.CallbackQuery, callback_data: SettingsAction):
    user = await _get_user(callback)

    @sync_to_async
    def get_schedules():
        return list(IncomeSchedule.objects.filter(user=user, deleted_at__isnull=True).order_by("day_of_month"))

    schedules = await get_schedules()
    if not schedules:
        await callback.message.edit_text(t("schedule.empty"), reply_markup=settings_menu_keyboard())
        await callback.answer()
        return

    lines = [t("schedule.list.title")]
    for schedule in schedules:
        status = "🟢" if schedule.is_active else "⚪"
        amount_text = f" — {schedule.expected_amount:.0f} ₽" if schedule.expected_amount else ""
        lines.append(f"{status} <b>{schedule.name}</b>: {schedule.day_of_month}-е число{amount_text}")

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=back_to_parent_keyboard(_BACK_TO_SETTINGS),
        parse_mode="HTML",
    )
    await callback.answer()


@settings_router.callback_query(SettingsAction.filter(F.action == SETTINGS_ADD_SCHEDULE))
async def add_schedule_start(callback: types.CallbackQuery, callback_data: SettingsAction, state: FSMContext, bot: Bot):
    await state.set_state(ScheduleStates.entering_name)
    await set_fsm_return_to(state, MENU_SETTINGS)
    await edit_and_track(callback.message, state, t("schedule.create.name_prompt"))
    await callback.answer()


@settings_router.message(ScheduleStates.entering_name)
async def schedule_enter_name(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)
    name = (message.text or "").strip()
    if not name:
        await send_and_track(bot, message.chat.id, state, t("error.empty_name"))
        return
    await state.update_data(schedule_name=name)
    await state.set_state(ScheduleStates.entering_day)
    await send_and_track(bot, message.chat.id, state, t("schedule.create.day_prompt", name=name))


@settings_router.message(ScheduleStates.entering_day)
async def schedule_enter_day(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)
    try:
        day = int((message.text or "").strip())
        if not 1 <= day <= 31:
            raise ValueError
    except ValueError:
        await send_and_track(bot, message.chat.id, state, t("error.invalid_day"))
        return
    await state.update_data(day_of_month=day)
    await state.set_state(ScheduleStates.entering_amount)
    await send_and_track(bot, message.chat.id, state, t("schedule.create.amount_prompt", day=str(day)))


@settings_router.message(ScheduleStates.entering_amount)
async def schedule_enter_amount(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)
    text = (message.text or "").strip().replace(" ", "")
    expected_amount = None
    if text != "-":
        try:
            expected_amount = Decimal(text)
            if expected_amount <= 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            await send_and_track(bot, message.chat.id, state, t("error.invalid_amount_or_skip"))
            return

    data = await state.get_data()
    user = await _get_user(message)

    @sync_to_async
    def create_schedule():
        return IncomeSchedule.objects.create(
            user=user, name=data["schedule_name"],
            day_of_month=data["day_of_month"], expected_amount=expected_amount,
        )

    schedule = await create_schedule()
    await cleanup_tracked(bot, state)
    await state.clear()
    amount_text = f"\n💰 Сумма: {schedule.expected_amount:.0f} ₽" if schedule.expected_amount else ""
    await send_temporary(
        bot, message.chat.id,
        t("schedule.create.success", name=schedule.name, day=str(schedule.day_of_month), amount_text=amount_text),
        delay_seconds=7,
    )
    await bot.send_message(message.chat.id, t("menu.settings.title"), reply_markup=settings_menu_keyboard())


# ═══════════════════════════════════════════════════════════
# Периоды отпуска
# ═══════════════════════════════════════════════════════════

@settings_router.callback_query(SettingsAction.filter(F.action == SETTINGS_VACATION))
async def vacation_list(callback: types.CallbackQuery, callback_data: SettingsAction):
    user = await _get_user(callback)

    @sync_to_async
    def get_vacations():
        return list(VacationPeriod.objects.filter(user=user, deleted_at__isnull=True).order_by("start_date"))

    vacations = await get_vacations()
    if not vacations:
        await callback.message.edit_text(t("vacation.empty"), reply_markup=settings_menu_keyboard())
        await callback.answer()
        return

    lines = [t("vacation.list.title")]
    inline_buttons = []
    for vacation in vacations:
        desc = f" — {vacation.description}" if vacation.description else ""
        lines.append(f"📅 {vacation.start_date} — {vacation.end_date} (×{vacation.budget_multiplier}){desc}")
        inline_buttons.append([
            types.InlineKeyboardButton(text=t("btn.vacation_edit"), callback_data=f"vacation_edit:{vacation.id}"),
            types.InlineKeyboardButton(text=t("btn.vacation_delete"), callback_data=f"vacation_delete:{vacation.id}"),
        ])
    inline_buttons.append([types.InlineKeyboardButton(text=t("btn.back"), callback_data=_BACK_TO_SETTINGS)])

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_buttons),
        parse_mode="HTML",
    )
    await callback.answer()


@settings_router.callback_query(SettingsAction.filter(F.action == SETTINGS_ADD_VACATION))
async def add_vacation_start(callback: types.CallbackQuery, callback_data: SettingsAction, state: FSMContext, bot: Bot):
    await state.set_state(VacationStates.entering_start_date)
    await set_fsm_return_to(state, MENU_SETTINGS)
    await edit_and_track(
        callback.message,
        state,
        t("vacation.create.start_prompt"),
        reply_markup=build_calendar_keyboard(),
    )
    await callback.answer()


@settings_router.message(VacationStates.entering_start_date)
async def vacation_enter_start(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)
    start_date = parse_user_date((message.text or "").strip())
    if not start_date:
        await send_and_track(bot, message.chat.id, state, t("error.invalid_date"))
        return
    await state.update_data(start_date=start_date.isoformat())
    await state.set_state(VacationStates.entering_end_date)
    await send_and_track(
        bot,
        message.chat.id,
        state,
        t("vacation.create.end_prompt", start_date=str(start_date)),
        reply_markup=build_calendar_keyboard(),
    )


@settings_router.callback_query(
    VacationStates.entering_start_date,
    CalendarAction.filter(F.action == CAL_SELECT_DAY),
)
async def vacation_calendar_start_selected(callback: types.CallbackQuery, callback_data: CalendarAction, state: FSMContext):
    selected_date = date(callback_data.year, callback_data.month, callback_data.day)
    await state.update_data(start_date=selected_date.isoformat())
    await state.set_state(VacationStates.entering_end_date)
    await callback.message.edit_text(
        t("vacation.create.end_prompt", start_date=str(selected_date)),
        reply_markup=build_calendar_keyboard(year=callback_data.year, month=callback_data.month),
        parse_mode="HTML",
    )
    await callback.answer()


@settings_router.message(VacationStates.entering_end_date)
async def vacation_enter_end(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)
    end_date = parse_user_date((message.text or "").strip())
    if not end_date:
        await send_and_track(bot, message.chat.id, state, t("error.invalid_date"))
        return
    data = await state.get_data()
    start_date = date.fromisoformat(data["start_date"])
    if end_date < start_date:
        await send_and_track(bot, message.chat.id, state, t("error.end_before_start"))
        return
    await state.update_data(end_date=end_date.isoformat())
    await state.set_state(VacationStates.entering_multiplier)
    await send_and_track(
        bot,
        message.chat.id,
        state,
        t("vacation.create.multiplier_prompt", start_date=str(start_date), end_date=str(end_date)),
    )


@settings_router.message(VacationStates.entering_multiplier)
async def vacation_enter_multiplier(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)
    text = (message.text or "").strip()
    multiplier = Decimal("1.50")
    if text != "-":
        try:
            multiplier = Decimal(text)
            if multiplier <= 0:
                raise ValueError
        except (InvalidOperation, ValueError):
            await send_and_track(bot, message.chat.id, state, t("error.invalid_multiplier"))
            return

    data = await state.get_data()
    user = await _get_user(message)
    vacation_id = data.get("vacation_id")

    @sync_to_async
    def save_vacation():
        if vacation_id:
            v = VacationPeriod.objects.filter(id=vacation_id, user=user).first()
            if v:
                v.start_date = date.fromisoformat(data["start_date"])
                v.end_date = date.fromisoformat(data["end_date"])
                v.budget_multiplier = multiplier
                v.save(update_fields=["start_date", "end_date", "budget_multiplier", "updated_at"])
                return v
        return VacationPeriod.objects.create(
            user=user, start_date=date.fromisoformat(data["start_date"]),
            end_date=date.fromisoformat(data["end_date"]), budget_multiplier=multiplier,
        )

    vacation = await save_vacation()
    await cleanup_tracked(bot, state)
    await state.clear()
    msg_text = t("vacation.edit.success" if vacation_id else "vacation.create.success",
                 start_date=str(vacation.start_date), end_date=str(vacation.end_date),
                 multiplier=str(vacation.budget_multiplier))
    await send_temporary(bot, message.chat.id, msg_text, delay_seconds=7)
    await bot.send_message(message.chat.id, t("menu.settings.title"), reply_markup=settings_menu_keyboard())


@settings_router.callback_query(
    VacationStates.entering_end_date,
    CalendarAction.filter(F.action == CAL_SELECT_DAY),
)
async def vacation_calendar_end_selected(callback: types.CallbackQuery, callback_data: CalendarAction, state: FSMContext):
    data = await state.get_data()
    start_date = date.fromisoformat(data["start_date"])
    end_date = date(callback_data.year, callback_data.month, callback_data.day)
    if end_date < start_date:
        await callback.answer(t("error.end_before_start"), show_alert=True)
        return
    await state.update_data(end_date=end_date.isoformat())
    await state.set_state(VacationStates.entering_multiplier)
    await callback.message.edit_text(
        t("vacation.create.multiplier_prompt", start_date=str(start_date), end_date=str(end_date)),
        parse_mode="HTML",
    )
    await callback.answer()


@settings_router.callback_query(
    VacationStates.entering_start_date,
    CalendarAction.filter(F.action.in_({CAL_PREV_MONTH, CAL_NEXT_MONTH})),
)
@settings_router.callback_query(
    VacationStates.entering_end_date,
    CalendarAction.filter(F.action.in_({CAL_PREV_MONTH, CAL_NEXT_MONTH})),
)
async def vacation_calendar_navigate(callback: types.CallbackQuery, callback_data: CalendarAction):
    await callback.message.edit_reply_markup(
        reply_markup=build_calendar_keyboard(year=callback_data.year, month=callback_data.month),
    )
    await callback.answer()


@settings_router.callback_query(
    VacationStates.entering_start_date,
    CalendarAction.filter(F.action == CAL_IGNORE),
)
@settings_router.callback_query(
    VacationStates.entering_end_date,
    CalendarAction.filter(F.action == CAL_IGNORE),
)
async def vacation_calendar_ignore(callback: types.CallbackQuery):
    await callback.answer()


# ─── Удаление периода отпуска ───────────────────────────

@settings_router.callback_query(F.data.startswith("vacation_delete:"))
async def vacation_delete_confirm_prompt(callback: types.CallbackQuery):
    vacation_id = int(callback.data.split(":")[1])
    user = await _get_user(callback)

    @sync_to_async
    def get_vacation():
        return VacationPeriod.objects.filter(id=vacation_id, user=user, deleted_at__isnull=True).first()

    vacation = await get_vacation()
    if not vacation:
        await callback.answer(t("error.not_found"), show_alert=True)
        return

    text = t("vacation.delete.confirm", start_date=str(vacation.start_date), end_date=str(vacation.end_date))
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(text=t("btn.vacation_delete_confirm"), callback_data=f"vacation_del_ok:{vacation_id}"),
            types.InlineKeyboardButton(text=t("btn.back"), callback_data=SettingsAction(action=SETTINGS_VACATION).pack()),
        ],
    ])
    await callback.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    await callback.answer()


@settings_router.callback_query(F.data.startswith("vacation_del_ok:"))
async def vacation_delete_confirmed(callback: types.CallbackQuery):
    vacation_id = int(callback.data.split(":")[1])
    user = await _get_user(callback)

    @sync_to_async
    def do_delete():
        v = VacationPeriod.objects.filter(id=vacation_id, user=user, deleted_at__isnull=True).first()
        if v:
            v.soft_delete()
        return v

    await do_delete()
    await callback.answer(t("vacation.delete.success"))
    await vacation_list(callback, SettingsAction(action=SETTINGS_VACATION))


# ─── Редактирование периода отпуска ─────────────────────

@settings_router.callback_query(F.data.startswith("vacation_edit:"))
async def vacation_edit_start(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    vacation_id = int(callback.data.split(":")[1])
    user = await _get_user(callback)

    @sync_to_async
    def get_vacation():
        return VacationPeriod.objects.filter(id=vacation_id, user=user, deleted_at__isnull=True).first()

    vacation = await get_vacation()
    if not vacation:
        await callback.answer(t("error.not_found"), show_alert=True)
        return

    await state.set_state(VacationStates.entering_start_date)
    await set_fsm_return_to(state, MENU_SETTINGS)
    await state.update_data(vacation_id=vacation_id)
    await edit_and_track(
        callback.message,
        state,
        t("vacation.create.start_prompt"),
        reply_markup=build_calendar_keyboard(),
    )
    await callback.answer()


# В vacation_enter_multiplier при наличии vacation_id в data — обновляем, иначе создаём

@settings_router.callback_query(SettingsAction.filter(F.action == SETTINGS_FAMILY))
async def family_info(callback: types.CallbackQuery, callback_data: SettingsAction):
    user = await _get_user(callback)
    groups = await FamilyGroupService.get_user_groups(user)

    if not groups:
        await callback.message.edit_text(t("family.empty"), reply_markup=settings_menu_keyboard())
        await callback.answer()
        return

    lines = [t("family.list.title")]
    inline_buttons = []

    for group in groups:
        members = await FamilyGroupService.get_group_members(group)
        user_membership = None
        member_lines = []
        for membership in members:
            role_icon = "👑" if membership.role == "admin" else "👤"
            display_name = membership.user.first_name or membership.user.username or str(membership.user.id)
            member_lines.append(f"  {role_icon} {display_name}")
            if membership.user.id == user.id:
                user_membership = membership

        notif_on = user_membership and user_membership.notifications_enabled
        notifications_status = "🔔 вкл" if notif_on else "🔕 выкл"

        lines.append(f"📌 <b>{group.name}</b>")
        lines.append(f"🔑 Код: <code>{group.invite_code}</code>")
        lines.append(f"📢 Уведомления: {notifications_status}")
        lines.append(f"👥 Участники ({len(members)}):")
        lines.extend(member_lines)
        lines.append("")

        notif_label = "🔕 Выкл. уведомления" if notif_on else "🔔 Вкл. уведомления"
        inline_buttons.append([
            types.InlineKeyboardButton(text=notif_label, callback_data=f"family_notif:{group.id}"),
            types.InlineKeyboardButton(text="🚪 Выйти", callback_data=f"family_leave:{group.id}"),
        ])

    inline_buttons.append([types.InlineKeyboardButton(text=t("btn.back"), callback_data=_BACK_TO_SETTINGS)])
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=inline_buttons),
        parse_mode="HTML",
    )
    await callback.answer()


@settings_router.callback_query(SettingsAction.filter(F.action == SETTINGS_CREATE_FAMILY))
async def family_create_start(callback: types.CallbackQuery, callback_data: SettingsAction, state: FSMContext, bot: Bot):
    await state.set_state(FamilyCreateStates.entering_name)
    await set_fsm_return_to(state, MENU_SETTINGS)
    await edit_and_track(callback.message, state, t("family.create.name_prompt"))
    await callback.answer()


@settings_router.message(FamilyCreateStates.entering_name)
async def family_create_name(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)
    name = (message.text or "").strip()
    if not name or len(name) > 100:
        await send_and_track(bot, message.chat.id, state, t("error.name_length"))
        return
    user = await _get_user(message)
    group = await FamilyGroupService.create_group(user, name)
    await cleanup_tracked(bot, state)
    await state.clear()
    await send_temporary(
        bot, message.chat.id,
        t("family.create.success", name=group.name, invite_code=group.invite_code),
        delay_seconds=15,
    )


@settings_router.callback_query(SettingsAction.filter(F.action == SETTINGS_JOIN_FAMILY))
async def family_join_start(callback: types.CallbackQuery, callback_data: SettingsAction, state: FSMContext, bot: Bot):
    await state.set_state(FamilyJoinStates.entering_code)
    await set_fsm_return_to(state, MENU_SETTINGS)
    await edit_and_track(callback.message, state, t("family.join.code_prompt"))
    await callback.answer()


@settings_router.message(FamilyJoinStates.entering_code)
async def family_join_code(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)
    code = (message.text or "").strip()
    if not code:
        await send_and_track(bot, message.chat.id, state, t("error.empty_code"))
        return
    user = await _get_user(message)
    membership = await FamilyGroupService.join_group(user, code)
    await cleanup_tracked(bot, state)
    await state.clear()
    if membership:
        await send_temporary(bot, message.chat.id, t("family.join.success", name=membership.group.name), delay_seconds=10)
    else:
        await send_temporary(bot, message.chat.id, t("family.join.failed"), delay_seconds=7)


# ─── Переключение уведомлений ─────────────────────────

@settings_router.callback_query(F.data.startswith("family_notif:"))
async def family_toggle_notifications(callback: types.CallbackQuery, bot: Bot):
    group_id = int(callback.data.split(":")[1])
    user = await _get_user(callback)

    @sync_to_async
    def get_group():
        from project.apps.core.models import FamilyGroup
        return FamilyGroup.objects.filter(id=group_id, deleted_at__isnull=True).first()

    group = await get_group()
    if not group:
        await callback.answer(t("error.group_not_found"), show_alert=True)
        return

    new_state = await FamilyGroupService.toggle_notifications(user, group)
    status_text = "включены 🔔" if new_state else "выключены 🔕"
    await callback.answer(f"Уведомления {status_text}")
    await family_info(callback, SettingsAction(action=SETTINGS_FAMILY))


# ─── Выход из группы ─────────────────────────────────

@settings_router.callback_query(F.data.startswith("family_leave:"))
async def family_leave(callback: types.CallbackQuery, bot: Bot):
    group_id = int(callback.data.split(":")[1])
    user = await _get_user(callback)

    @sync_to_async
    def get_group():
        from project.apps.core.models import FamilyGroup
        return FamilyGroup.objects.filter(id=group_id, deleted_at__isnull=True).first()

    group = await get_group()
    if not group:
        await callback.answer(t("error.group_not_found"), show_alert=True)
        return

    success = await FamilyGroupService.leave_group(user, group)
    if success:
        await callback.answer(f"Вы вышли из «{group.name}»")
        await family_info(callback, SettingsAction(action=SETTINGS_FAMILY))
    else:
        await callback.answer(t("family.leave.admin_error"), show_alert=True)
