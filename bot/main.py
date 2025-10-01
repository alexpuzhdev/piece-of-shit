import os
import asyncio
import django
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.config.settings")
django.setup()

from bot.handlers.start_handler import StartHandler

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

StartHandler(dp)

async def main():
    print("🤖 Bot started polling...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
