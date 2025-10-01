import django
import os
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.config.settings")
django.setup()
BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

from bot.core.setup import setup_handlers

async def main():
    print("🤖 Bot started polling...")
    setup_handlers(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
