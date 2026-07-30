from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.config import settings
from bot.database import get_session
from bot.models import User, Booking, Service, TimeSlot, ContestEntry
from bot.keyboards.reply import get_admin_keyboard, get_booking_status_keyboard

router = Router()


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != settings.admin_chat_id:
        await message.answer("❌ У вас нет доступа.")
        return
    
    await show_bookings(message, "all")


@router.callback_query(F.data.startswith("admin_"))
async def admin_callback(callback: CallbackQuery):
    if callback.from_user.id != settings.admin_chat_id:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.answer()
    
    if callback.data == "admin_all":
        await show_bookings(callback, "all")
    elif callback.data == "admin_pending":
        await show_bookings(callback, "pending")
    elif callback.data == "admin_completed":
        await show_bookings(callback, "completed")
    elif callback.data == "admin_contest":
        await show_contest_entries(callback)


async def show_bookings(event, filter_type: str):
    async with get_session() as session:
        query = select(Booking).join(User).join(Service).join(TimeSlot)
        
        if filter_type == "pending":
            query = query.where(Booking.status.in_(["new", "confirmed"]))
        elif filter_type == "completed":
            query = query.where(Booking.status.in_(["completed", "cancelled"]))
        
        query = query.order_by(Booking.created_at.desc())
        result = await session.execute(query)
        bookings = result.scalars().all()
    
    if not bookings:
        text = "📋 Записей не найдено."
    else:
        text = f"📋 <b>Записи ({filter_type}):</b>\n\n"
        for b in bookings:
            status_emoji = {"new": "🆕", "confirmed": "✅", "completed": "✅", "cancelled": "❌"}.get(b.status, "❓")
            text += (
                f"{status_emoji} <b>#{b.id}</b> — {b.service.name}\n"
                f"📅 {b.time_slot.date.strftime('%d.%m.%Y')} {b.time_slot.start_time}\n"
                f"👤 {b.client_name} | 📱 {b.client_phone}\n"
                f"👤 @{b.user.username or b.user.first_name}\n"
                f"Статус: {b.status}\n\n"
            )
    
    if isinstance(event, Message):
        await event.answer(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
    else:
        await event.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")


async def show_contest_entries(event):
    async with get_session() as session:
        result = await session.execute(
            select(ContestEntry).join(User).order_by(ContestEntry.created_at.desc())
        )
        entries = result.scalars().all()
    
    if not entries:
        text = "🎁 Участников конкурса пока нет."
    else:
        text = "🎁 <b>Участники конкурса:</b>\n\n"
        for e in entries:
            text += (
                f"👤 @{e.user.username or e.user.first_name}\n"
                f"💬 {e.answer}\n"
                f"📅 {e.created_at.strftime('%d.%m.%Y %H:%M')}\n\n"
            )
    
    if isinstance(event, Message):
        await event.answer(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")
    else:
        await event.message.edit_text(text, reply_markup=get_admin_keyboard(), parse_mode="HTML")


@router.callback_query(F.data.startswith("booking_"))
async def booking_action(callback: CallbackQuery):
    if callback.from_user.id != settings.admin_chat_id:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    
    await callback.answer()
    
    action, booking_id = callback.data.split("_")[1], int(callback.data.split("_")[2])
    
    async with get_session() as session:
        result = await session.execute(select(Booking).where(Booking.id == booking_id))
        booking = result.scalar_one_or_none()
        
        if not booking:
            await callback.message.edit_text("❌ Запись не найдена.", reply_markup=get_admin_keyboard())
            return
        
        if action == "complete":
            booking.status = "completed"
            await session.commit()
            try:
                await callback.bot.send_message(
                    booking.user.telegram_id,
                    f"✅ Ваша запись #{booking.id} выполнена!\n"
                    f"{booking.service.name} — {booking.time_slot.date.strftime('%d.%m.%Y')} {booking.time_slot.start_time}"
                )
            except Exception:
                pass
            await callback.message.edit_text(f"✅ Запись #{booking_id} выполнена.", reply_markup=get_admin_keyboard())
        
        elif action == "cancel":
            booking.status = "cancelled"
            await session.commit()
            try:
                await callback.bot.send_message(
                    booking.user.telegram_id,
                    f"❌ Ваша запись #{booking.id} отменена.\n"
                    f"{booking.service.name} — {booking.time_slot.date.strftime('%d.%m.%Y')} {booking.time_slot.start_time}"
                )
            except Exception:
                pass
            await callback.message.edit_text(f"❌ Запись #{booking_id} отменена.", reply_markup=get_admin_keyboard())