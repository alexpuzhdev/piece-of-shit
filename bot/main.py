import asyncio
import logging
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.config.settings")
django.setup()

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from bot.core.scheduler import run_daily_reminders
from bot.core.setup import setup_handlers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())


async def main():
    logger.info("Bot starting...")

    setup_handlers(dp)

    # Загружаем тексты бота из БД (с fallback на дефолты)
    from bot.core.texts.registry import BotTextRegistry
    await BotTextRegistry.load()

    # Запускаем фоновую задачу напоминаний
    reminder_task = asyncio.create_task(run_daily_reminders(bot))

    try:
        await dp.start_polling(bot)
    finally:
        reminder_task.cancel()
        try:
            await reminder_task
        except asyncio.CancelledError:
            pass
        logger.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
