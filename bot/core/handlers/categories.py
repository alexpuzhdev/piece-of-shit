"""Управление категориями: список, создание, переименование, удаление."""

from aiogram import Router, types, Bot, F
from aiogram.fsm.context import FSMContext

from bot.core.callbacks.menu import (
    SettingsAction, CategoryAction, MenuAction,
    SETTINGS_CATEGORIES, CAT_RENAME, CAT_DELETE, CAT_DELETE_CONFIRM,
    MENU_SETTINGS,
)
from bot.core.states.category_states import CategoryRenameStates, CategoryCreateStates
from bot.core.texts import t
from bot.services.fsm_message_tracker import (
    edit_and_track, send_and_track, cleanup_tracked, send_temporary, set_fsm_return_to,
)
from bot.services.message_service import MessageService
from project.apps.expenses.models import Category
from project.apps.expenses.services.category_service import CategoryService

categories_router = Router()

_BACK_TO_SETTINGS = MenuAction(action=MENU_SETTINGS).pack()
_BACK_TO_CATEGORIES = SettingsAction(action=SETTINGS_CATEGORIES).pack()

# Отдельный action для создания из CRUD-меню (не путаем с CAT_ADD_NEW из expenses)
CAT_CREATE_FROM_MANAGEMENT = "mgmt_create"


# ─── Список категорий ──────────────────────────────────

@categories_router.callback_query(SettingsAction.filter(F.action == SETTINGS_CATEGORIES))
async def category_list(callback: types.CallbackQuery, callback_data: SettingsAction):
    categories = await CategoryService.get_all_categories()

    if not categories:
        await callback.message.edit_text(
            t("categories.empty"),
            reply_markup=_categories_keyboard([]),
        )
        await callback.answer()
        return

    lines = [t("categories.list.title", count=str(len(categories)))]
    for cat in categories:
        lines.append(f"  📁 {cat.name}")

    buttons = []
    for cat in categories:
        if cat.name == "Прочее":
            continue
        buttons.append([
            types.InlineKeyboardButton(
                text=f"✏️ {cat.name}",
                callback_data=CategoryAction(action=CAT_RENAME, category_id=cat.id).pack(),
            ),
            types.InlineKeyboardButton(
                text="🗑",
                callback_data=CategoryAction(action=CAT_DELETE, category_id=cat.id).pack(),
            ),
        ])

    buttons.append([
        types.InlineKeyboardButton(
            text=t("btn.category_add"),
            callback_data=CategoryAction(action=CAT_CREATE_FROM_MANAGEMENT, category_id=0).pack(),
        ),
    ])
    buttons.append([
        types.InlineKeyboardButton(text=t("btn.back"), callback_data=_BACK_TO_SETTINGS),
    ])

    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=buttons),
    )
    await callback.answer()


def _categories_keyboard(extra_buttons: list) -> types.InlineKeyboardMarkup:
    buttons = list(extra_buttons)
    buttons.append([
        types.InlineKeyboardButton(
            text=t("btn.category_add"),
            callback_data=CategoryAction(action=CAT_CREATE_FROM_MANAGEMENT, category_id=0).pack(),
        ),
    ])
    buttons.append([
        types.InlineKeyboardButton(text=t("btn.back"), callback_data=_BACK_TO_SETTINGS),
    ])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── Создание категории ────────────────────────────────

@categories_router.callback_query(CategoryAction.filter(F.action == CAT_CREATE_FROM_MANAGEMENT))
async def category_create_start_from_management(callback: types.CallbackQuery, callback_data: CategoryAction, state: FSMContext, bot: Bot):
    """Создание новой категории из раздела управления."""

    await state.set_state(CategoryCreateStates.entering_name)
    await set_fsm_return_to(state, MENU_SETTINGS)
    await edit_and_track(callback.message, state, t("categories.create.prompt"))
    await callback.answer()


@categories_router.message(CategoryCreateStates.entering_name)
async def category_create_name(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)

    name = (message.text or "").strip()
    if not name:
        await send_and_track(bot, message.chat.id, state, t("error.empty_name"))
        return

    exists = await CategoryService.category_exists(name)
    if exists:
        await send_and_track(bot, message.chat.id, state, t("categories.create.exists", name=name.title()))
        return

    category = await CategoryService.create_category(name)
    await cleanup_tracked(bot, state)
    await state.clear()
    await send_temporary(bot, message.chat.id, t("categories.create.success", name=category.name))


# ─── Переименование категории ──────────────────────────

@categories_router.callback_query(CategoryAction.filter(F.action == CAT_RENAME))
async def category_rename_start(callback: types.CallbackQuery, callback_data: CategoryAction, state: FSMContext, bot: Bot):
    category = await Category.objects.filter(id=callback_data.category_id).afirst()
    if not category:
        await callback.answer(t("error.category_not_found"), show_alert=True)
        return

    await state.set_state(CategoryRenameStates.entering_new_name)
    await set_fsm_return_to(state, MENU_SETTINGS)
    await state.update_data(rename_category_id=category.id, rename_category_old_name=category.name)
    await edit_and_track(callback.message, state, t("categories.rename.prompt", name=category.name))
    await callback.answer()


@categories_router.message(CategoryRenameStates.entering_new_name)
async def category_rename_done(message: types.Message, state: FSMContext, bot: Bot):
    tool_box = MessageService(bot)
    await tool_box.cleaner.delete_user_message(message)

    new_name = (message.text or "").strip()
    if not new_name:
        await send_and_track(bot, message.chat.id, state, t("error.empty_name"))
        return

    data = await state.get_data()
    category_id = data["rename_category_id"]
    old_name = data["rename_category_old_name"]

    category = await Category.objects.filter(id=category_id).afirst()
    if not category:
        await cleanup_tracked(bot, state)
        await state.clear()
        await send_temporary(bot, message.chat.id, t("error.category_not_found"))
        return

    category = await CategoryService.rename_category(category, new_name)
    await cleanup_tracked(bot, state)
    await state.clear()
    await send_temporary(bot, message.chat.id, t("categories.rename.success", old_name=old_name, new_name=category.name))


# ─── Удаление категории ────────────────────────────────

@categories_router.callback_query(CategoryAction.filter(F.action == CAT_DELETE))
async def category_delete_confirm_prompt(callback: types.CallbackQuery, callback_data: CategoryAction):
    category = await Category.objects.filter(id=callback_data.category_id).afirst()
    if not category:
        await callback.answer(t("error.category_not_found"), show_alert=True)
        return

    confirm_keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
        [
            types.InlineKeyboardButton(
                text=t("btn.category_delete_confirm"),
                callback_data=CategoryAction(action=CAT_DELETE_CONFIRM, category_id=category.id).pack(),
            ),
            types.InlineKeyboardButton(
                text=t("btn.back"),
                callback_data=_BACK_TO_CATEGORIES,
            ),
        ],
    ])
    await callback.message.edit_text(
        t("categories.delete.confirm", name=category.name),
        reply_markup=confirm_keyboard,
    )
    await callback.answer()


@categories_router.callback_query(CategoryAction.filter(F.action == CAT_DELETE_CONFIRM))
async def category_delete_confirmed(callback: types.CallbackQuery, callback_data: CategoryAction):
    category = await Category.objects.filter(id=callback_data.category_id).afirst()
    if not category:
        await callback.answer(t("error.category_not_found"), show_alert=True)
        return

    name = category.name
    await CategoryService.delete_category(category)
    await callback.answer(t("categories.delete.success", name=name))

    # Возвращаемся к списку категорий
    await category_list(callback, SettingsAction(action=SETTINGS_CATEGORIES))
