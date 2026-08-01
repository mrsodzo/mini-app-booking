import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.database import init_db, close_db, async_session_maker
from bot.handlers import router as main_router
from bot.init_data import init_default_data, ensure_time_slots, ensure_admin


logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def main():
    if not settings.bot_token or settings.bot_token == "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz":
        logger.error("BOT_TOKEN not set! Please create .env file from .env.example")
        return
    
    # Initialize DB before starting bot
    await init_db()
    async with async_session_maker() as session:
        await init_default_data(session)
        await ensure_time_slots(session)
        await ensure_admin(session)
    logger.info("Database initialized")
    
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(main_router)
    
    @dp.update()
    async def log_update(update, data):
        logger.debug(f"UPDATE: {update.update_id}, type: {type(update).__name__}")
        if update.message:
            logger.debug(f"  Message: {update.message.message_id}, web_app_data: {bool(update.message.web_app_data)}, text: {update.message.text}")
        if update.callback_query:
            logger.debug(f"  Callback: {update.callback_query.data}")
    
    logger.info("Starting bot...")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await close_db()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")