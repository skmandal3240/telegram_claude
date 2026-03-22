import asyncio
import logging
import sys

from aiogram import BaseMiddleware, Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, TelegramObject

import config
from database.db import init_db
from services import scheduler_service
from handlers import start, chat, scrape, content, automation

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

dp = Dispatcher()


class AccessControlMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        if config.ALLOWED_USER_IDS:
            user = data.get("event_from_user")
            if user and user.id not in config.ALLOWED_USER_IDS:
                return  # silently ignore unauthorized users
        return await handler(event, data)


dp.message.middleware(AccessControlMiddleware())

# Include routers (order matters - commands first, then catch-all chat)
dp.include_router(start.router)
dp.include_router(scrape.router)
dp.include_router(content.router)
dp.include_router(automation.router)
dp.include_router(chat.router)  # catch-all must be last


async def main():
    if not config.BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set. Copy .env.example to .env and fill in your token.")
        sys.exit(1)

    if not config.AUTH_TOKEN:
        logger.error("No Claude API auth found. Run inside Claude Code cloud or set ANTHROPIC_API_KEY.")
        sys.exit(1)

    logger.info("Initializing database...")
    await init_db()

    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=None))

    logger.info("Starting scheduler...")
    scheduler_service.set_bot(bot)
    await scheduler_service.start_scheduler()

    logger.info("Bot is starting... Send /start in Telegram!")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
