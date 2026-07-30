from aiogram import Router

from bot.handlers.start import router as start_router
from bot.handlers.booking import router as booking_router
from bot.handlers.contest import router as contest_router
from bot.handlers.admin import router as admin_router

router = Router()
router.include_router(start_router)
router.include_router(booking_router)
router.include_router(contest_router)
router.include_router(admin_router)