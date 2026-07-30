import asyncio
import logging
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.database import init_db, close_db, async_session_maker
from bot.handlers import router as main_router
from bot.init_data import init_default_data


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan():
    await init_db()
    
    async with async_session_maker() as session:
        await init_default_data(session)
    
    logger.info("Database initialized")
    yield
    await close_db()


async def main():
    if not settings.bot_token or settings.bot_token == "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz":
        logger.error("BOT_TOKEN not set! Please create .env file from .env.example")
        return
    
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(main_router)
    
    logger.info("Starting bot...")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped")