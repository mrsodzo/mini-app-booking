from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from bot.config import settings
from bot.database import get_session
from bot.models import User, Booking, ContestEntry
from bot.keyboards.reply import (
    get_start_keyboard,
    get_admin_keyboard,
    get_booking_status_keyboard,
    get_back_to_start_keyboard,
)

router = Router()
logger = logging.getLogger(__name__)


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    
    async for session in get_session():
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            user = User(
                telegram_id=message.from_user.id,
                username=message.from_user.username,
                first_name=message.from_user.first_name,
                last_name=message.from_user.last_name,
            )
            session.add(user)
            await session.commit()
    
    text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Добро пожаловать в <b>Beauty Studio</b> 💇‍♀️\n\n"
        f"Здесь вы можете:\n"
        f"📅 Записаться на услугу\n"
        f"📋 Посмотреть свои записи\n"
        f"🎁 Участвовать в конкурсе и выиграть скидку 20%\n\n"
        f"Выберите действие:"
    )
    
    await message.answer(text, reply_markup=get_start_keyboard(), parse_mode="HTML")


@router.message(F.text == "📋 Мои записи")
async def show_my_bookings(message: Message):
    async for session in get_session():
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await message.answer(
                "❌ Пользователь не найден. Нажмите /start",
                reply_markup=get_start_keyboard(),
            )
            return
        
        result = await session.execute(
            select(Booking)
            .where(Booking.user_id == user.id)
            .options(selectinload(Booking.service), selectinload(Booking.time_slot))
            .order_by(Booking.created_at.desc())
        )
        bookings = result.scalars().all()
    
    if not bookings:
        await message.answer(
            "📋 У вас пока нет записей.\n\nНажмите кнопку ниже, чтобы записаться!",
            reply_markup=get_start_keyboard(),
        )
        return
    
    text = "📋 <b>Ваши записи:</b>\n\n"
    for booking in bookings:
        status_emoji = {
            "new": "🆕",
            "confirmed": "✅",
            "completed": "✅",
            "cancelled": "❌",
        }.get(booking.status, "❓")
        
        text += (
            f"{status_emoji} <b>#{booking.id}</b> — {booking.service.name}\n"
            f"📅 {booking.time_slot.date.strftime('%d.%m.%Y')} в {booking.time_slot.start_time}\n"
            f"Статус: {booking.status}\n\n"
        )
    
    await message.answer(text, reply_markup=get_start_keyboard(), parse_mode="HTML")


@router.message(F.text == "💇 Услуги")
async def show_services(message: Message):
    await message.answer(
        "💇 <b>Наши услуги:</b>\n\n"
        "✂️ <b>Стрижка мужская</b> — 1500₽ (30 мин)\n"
        "🧔 <b>Стрижка бороды</b> — 800₽ (20 мин)\n"
        "🎨 <b>Окрашивание волос</b> — 4500₽ (90 мин)\n"
        "✨ <b>Укладка волос</b> — 1000₽ (30 мин)\n"
        "💇+🧔 <b>Комплекс: стрижка + борода</b> — 2000₽ (45 мин)\n\n"
        "Нажмите кнопку ниже, чтобы записаться!",
        reply_markup=get_start_keyboard(),
        parse_mode="HTML",
    )


@router.message(F.text == "📞 Контакты")
async def show_contacts(message: Message):
    await message.answer(
        "📞 <b>Контакты</b>\n\n"
        "📍 Наш салон: ул. Примерная, д. 1\n"
        "📱 Телефон: +7 (999) 123-45-67\n"
        "🕐 Режим работы: ежедневно 10:00–21:00\n\n"
        "Мы всегда на связи!",
        reply_markup=get_start_keyboard(),
        parse_mode="HTML",
    )


@router.message(F.text == "⬅️ В главное меню")
async def back_to_start(message: Message):
    text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        f"Добро пожаловать в <b>Beauty Studio</b> 💇‍♀️\n\n"
        f"Здесь вы можете:\n"
        f"📅 Записаться на услугу\n"
        f"📋 Посмотреть свои записи\n"
        f"🎁 Участвовать в конкурсе и выиграть скидку 20%\n\n"
        f"Выберите действие:"
    )
    
    await message.answer(text, reply_markup=get_start_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "back_to_start")
async def back_to_start_callback(callback: CallbackQuery):
    await callback.answer()
    
    text = (
        f"👋 Привет, {callback.from_user.first_name}!\n\n"
        f"Добро пожаловать в <b>Beauty Studio</b> 💇‍♀️\n\n"
        f"Здесь вы можете:\n"
        f"📅 Записаться на услугу\n"
        f"📋 Посмотреть свои записи\n"
        f"🎁 Участвовать в конкурсе и выиграть скидку 20%\n\n"
        f"Выберите действие:"
    )
    
    await callback.message.edit_text(text, reply_markup=get_start_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "my_bookings")
async def show_my_bookings_callback(callback: CallbackQuery):
    await callback.answer()
    
    async for session in get_session():
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            await callback.message.edit_text(
                "❌ Пользователь не найден. Нажмите /start",
                reply_markup=get_back_to_start_keyboard(),
            )
            return
        
        result = await session.execute(
            select(Booking)
            .where(Booking.user_id == user.id)
            .options(selectinload(Booking.service), selectinload(Booking.time_slot))
            .order_by(Booking.created_at.desc())
        )
        bookings = result.scalars().all()
    
    if not bookings:
        await callback.message.edit_text(
            "📋 У вас пока нет записей.\n\nНажмите кнопку ниже, чтобы записаться!",
            reply_markup=get_start_keyboard(),
        )
        return
    
    text = "📋 <b>Ваши записи:</b>\n\n"
    for booking in bookings:
        status_emoji = {
            "new": "🆕",
            "confirmed": "✅",
            "completed": "✅",
            "cancelled": "❌",
        }.get(booking.status, "❓")
        
        text += (
            f"{status_emoji} <b>#{booking.id}</b> — {booking.service.name}\n"
            f"📅 {booking.time_slot.date.strftime('%d.%m.%Y')} в {booking.time_slot.start_time}\n"
            f"Статус: {booking.status}\n\n"
        )
    
    await callback.message.edit_text(text, reply_markup=get_back_to_start_keyboard(), parse_mode="HTML")


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != settings.admin_chat_id:
        await message.answer("❌ У вас нет доступа к админке.")
        return
    
    async for session in get_session():
        result = await session.execute(
            select(Booking)
            .options(
                selectinload(Booking.service),
                selectinload(Booking.time_slot)
            )
            .order_by(Booking.created_at.desc())
            .limit(20)
        )
        bookings = result.scalars().all()
    
    if not bookings:
        await message.answer(
            "📋 Записей пока нет.",
            reply_markup=get_admin_keyboard(),
        )
        return
    
    text = "📋 <b>Последние записи:</b>\n\n"
    for booking in bookings:
        status_emoji = {
            "new": "🆕",
            "confirmed": "✅",
            "completed": "✅",
            "cancelled": "❌",
        }.get(booking.status, "❓")
        
        text += (
            f"{status_emoji} <b>#{booking.id}</b> — {booking.service.name}\n"
            f"📅 {booking.time_slot.date.strftime('%d.%m.%Y')} в {booking.time_slot.start_time}\n"
            f"👤 {booking.client_name} | 📱 {booking.client_phone}\n"
            f"Статус: {booking.status}\n\n"
        )
    
    await message.answer(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")


@router.callback_query(F.data.startswith("admin_"))
async def admin_callbacks(callback: CallbackQuery):
    await callback.answer()
    
    if callback.from_user.id != settings.admin_chat_id:
        await callback.message.edit_text("❌ У вас нет доступа.")
        return
    
    async for session in get_session():
        if callback.data == "admin_all_bookings":
            result = await session.execute(
                select(Booking)
                .options(
                    selectinload(Booking.service),
                    selectinload(Booking.time_slot)
                )
                .order_by(Booking.created_at.desc())
            )
            bookings = result.scalars().all()
            status_filter = "Все"
        elif callback.data == "admin_pending_bookings":
            result = await session.execute(
                select(Booking)
                .options(
                    selectinload(Booking.service),
                    selectinload(Booking.time_slot)
                )
                .where(Booking.status.in_(["new", "confirmed"]))
                .order_by(Booking.created_at.desc())
            )
            bookings = result.scalars().all()
            status_filter = "Ожидающие"
        elif callback.data == "admin_completed_bookings":
            result = await session.execute(
                select(Booking)
                .options(
                    selectinload(Booking.service),
                    selectinload(Booking.time_slot)
                )
                .where(Booking.status.in_(["completed", "cancelled"]))
                .order_by(Booking.created_at.desc())
            )
            bookings = result.scalars().all()
            status_filter = "Завершённые"
        else:
            return
    
    if not bookings:
        await callback.message.edit_text(
            f"📋 {status_filter} записей нет.",
            reply_markup=get_admin_keyboard(),
        )
        return
    
    text = f"📋 <b>{status_filter} записи:</b>\n\n"
    for booking in bookings:
        status_emoji = {
            "new": "🆕",
            "confirmed": "✅",
            "completed": "✅",
            "cancelled": "❌",
        }.get(booking.status, "❓")
        
        text += (
            f"{status_emoji} <b>#{booking.id}</b> — {booking.service.name}\n"
            f"📅 {booking.time_slot.date.strftime('%d.%m.%Y')} в {booking.time_slot.start_time}\n"
            f"👤 {booking.client_name} | 📱 {booking.client_phone}\n"
            f"Статус: {booking.status}\n\n"
        )
    
    await callback.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")


@router.callback_query(F.data.startswith("booking_complete_"))
async def complete_booking(callback: CallbackQuery):
    await callback.answer()
    
    if callback.from_user.id != settings.admin_chat_id:
        await callback.message.edit_text("❌ У вас нет доступа.")
        return
    
    booking_id = int(callback.data.split("_")[-1])
    
    async for session in get_session():
        result = await session.execute(
            select(Booking)
            .options(
                selectinload(Booking.user),
                selectinload(Booking.service),
                selectinload(Booking.time_slot)
            )
            .where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            await callback.message.edit_text(
                "❌ Запись не найдена.",
                reply_markup=get_admin_keyboard(),
            )
            return
        
        booking.status = "completed"
        await session.commit()
        
        try:
            await callback.bot.send_message(
                booking.user.telegram_id,
                f"✅ Ваша запись #{booking.id} отмечена как выполненная!\n"
                f"Услуга: {booking.service.name}\n"
                f"Дата: {booking.time_slot.date.strftime('%d.%m.%Y')} в {booking.time_slot.start_time}",
            )
        except Exception:
            pass
        
        await callback.message.edit_text(
            f"✅ Запись #{booking.id} отмечена как выполненная.",
            reply_markup=get_admin_keyboard(),
        )


@router.callback_query(F.data.startswith("booking_cancel_"))
async def cancel_booking_admin(callback: CallbackQuery):
    await callback.answer()
    
    if callback.from_user.id != settings.admin_chat_id:
        await callback.message.edit_text("❌ У вас нет доступа.")
        return
    
    booking_id = int(callback.data.split("_")[-1])
    
    async for session in get_session():
        result = await session.execute(
            select(Booking)
            .options(
                selectinload(Booking.user),
                selectinload(Booking.service),
                selectinload(Booking.time_slot)
            )
            .where(Booking.id == booking_id)
        )
        booking = result.scalar_one_or_none()
        
        if not booking:
            await callback.message.edit_text(
                "❌ Запись не найдена.",
                reply_markup=get_admin_keyboard(),
            )
            return
        
        booking.status = "cancelled"
        await session.commit()
        
        try:
            await callback.bot.send_message(
                booking.user.telegram_id,
                f"❌ Ваша запись #{booking.id} была отменена администратором.\n"
                f"Услуга: {booking.service.name}\n"
                f"Дата: {booking.time_slot.date.strftime('%d.%m.%Y')} в {booking.time_slot.start_time}",
            )
        except Exception:
            pass
        
        await callback.message.edit_text(
            f"❌ Запись #{booking.id} отменена.",
            reply_markup=get_admin_keyboard(),
        )