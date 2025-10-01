import django
import os
import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.config.settings")
django.setup()
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()


async def main():
    logger.info("🤖 Bot started polling...")
    from bot.core.handlers.start_handler import start
    dp.include_routers(
        start
    )
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
