from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from bot.config import settings


def get_start_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📅 Записаться", web_app=WebAppInfo(url=f"{settings.webapp_url}/booking.html")),
            ],
            [
                KeyboardButton(text="📋 Мои записи"),
                KeyboardButton(text="💇 Услуги"),
            ],
            [
                KeyboardButton(text="🎁 Конкурс (скидка 20%)", web_app=WebAppInfo(url=f"{settings.webapp_url}/contest.html")),
            ],
            [
                KeyboardButton(text="📞 Контакты"),
            ],
        ],
        resize_keyboard=True,
    )


def get_services_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💇 Стрижка мужская — 1500₽",
                web_app=WebAppInfo(url=f"{settings.webapp_url}/booking.html?service=haircut"),
            ),
        ],
        [
            InlineKeyboardButton(
                text="🧔 Стрижка бороды — 800₽",
                web_app=WebAppInfo(url=f"{settings.webapp_url}/booking.html?service=beard"),
            ),
        ],
        [
            InlineKeyboardButton(
                text="🎨 Окрашивание — 4500₽",
                web_app=WebAppInfo(url=f"{settings.webapp_url}/booking.html?service=coloring"),
            ),
        ],
        [
            InlineKeyboardButton(
                text="✨ Укладка — 1000₽",
                web_app=WebAppInfo(url=f"{settings.webapp_url}/booking.html?service=styling"),
            ),
        ],
        [
            InlineKeyboardButton(
                text="💇+🧔 Комплекс — 2000₽",
                web_app=WebAppInfo(url=f"{settings.webapp_url}/booking.html?service=combo"),
            ),
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start"),
        ],
    ])


def get_contest_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🎁 Участвовать в конкурсе",
                web_app=WebAppInfo(url=f"{settings.webapp_url}/contest.html"),
            ),
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start"),
        ],
    ])


def get_contacts_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start"),
        ],
    ])


def get_my_bookings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Отменить запись", callback_data="cancel_booking"),
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start"),
        ],
    ])


def get_back_to_start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⬅️ В главное меню", callback_data="back_to_start"),
        ],
    ])


def get_webapp_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📅 Записаться", web_app=WebAppInfo(url=f"{settings.webapp_url}/booking.html"))],
            [KeyboardButton(text="🎁 Конкурс", web_app=WebAppInfo(url=f"{settings.webapp_url}/contest.html"))],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )


def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Все записи", callback_data="admin_all"),
        ],
        [
            InlineKeyboardButton(text="⏳ Ожидающие", callback_data="admin_pending"),
        ],
        [
            InlineKeyboardButton(text="✅ Выполненные", callback_data="admin_completed"),
        ],
        [
            InlineKeyboardButton(text="🎁 Участники конкурса", callback_data="admin_contest"),
        ],
    ])


def get_booking_status_keyboard(booking_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Выполнено",
                callback_data=f"booking_complete_{booking_id}",
            ),
            InlineKeyboardButton(
                text="❌ Отменить",
                callback_data=f"booking_cancel_{booking_id}",
            ),
        ],
        [
            InlineKeyboardButton(text="🔙 Назад", callback_data="admin_all"),
        ],
    ])