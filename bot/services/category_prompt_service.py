from aiogram import types, Bot

from bot.core.callbacks.menu import CategoryAction, CAT_ADD_NEW, CAT_ADD_ALIAS, CAT_USE_OTHER
from bot.core.texts import t
from project.apps.expenses.services.category_service import CategoryService


async def prompt_unknown_category(bot: Bot, chat_id: int, category_text: str) -> None:
    if not category_text or category_text in ("Без категории", "Без описания"):
        return

    match_result = await CategoryService.match(category_text)
    if not match_result.fell_back_to_other:
        return

    all_categories = await CategoryService.get_all_categories()
    category_buttons = []
    for cat in all_categories[:6]:
        if cat.name == "Прочее":
            continue
        category_buttons.append([
            types.InlineKeyboardButton(
                text=f"📁 {cat.name}",
                callback_data=CategoryAction(action=CAT_ADD_ALIAS, category_id=cat.id).pack(),
            ),
        ])

    category_buttons.append([
        types.InlineKeyboardButton(
            text=t("btn.category_create", name=category_text[:20]),
            callback_data=CategoryAction(action=CAT_ADD_NEW).pack(),
        ),
    ])
    category_buttons.append([
        types.InlineKeyboardButton(
            text=t("btn.category_keep_other"),
            callback_data=CategoryAction(action=CAT_USE_OTHER).pack(),
        ),
    ])

    await bot.send_message(
        chat_id=chat_id,
        text=t("category.unknown_prompt", category=category_text),
        reply_markup=types.InlineKeyboardMarkup(inline_keyboard=category_buttons),
    )
